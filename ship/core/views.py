from datetime import date as date_type, datetime as datetime_type
from decimal import Decimal

from django.conf import settings
from django.db.models import DecimalField, F, Q, Value
from django.db.models.functions import Coalesce
from django.db.models.expressions import ExpressionWrapper
from django.utils import timezone as tz
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import Image, Order, OrderImage, OrderStyle, OrderText, Text
from .serializers import OrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    当前登录用户的订单列表 + 新建。
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        列表查询：
        - 仅返回当前登录用户的订单
        - 支持按 tracking_number 精确/模糊（见 search_tracking）
        - 支持按 is_completed（true/false/1/0）过滤
        - 支持按订单文字标签搜索：search_text，在 OrderText 关联的 Text.context 中 icontains
        - 支持按完成日期：completed_date_from（YYYY-MM-DD）、completed_date_to
        - 支持按客户：customer_id
        - 支持按成本/售价：cost_min、cost_max、price_min、price_max
        - 支持按利润：profit_min、profit_max（利润 = 售价 - 成本，null 按 0 参与计算）
        """
        qs = Order.objects.filter(user=self.request.user)

        tracking_number = (self.request.query_params.get("tracking_number") or "").strip()
        if tracking_number:
            # 支持模糊：若前端传 search_tracking=1 则 icontains，否则精确
            search_tracking = self.request.query_params.get("search_tracking", "")
            if str(search_tracking).lower() in ("true", "1"):
                qs = qs.filter(tracking_number__icontains=tracking_number)
            else:
                qs = qs.filter(tracking_number=tracking_number)

        search_text = (self.request.query_params.get("search_text") or "").strip()
        if search_text:
            qs = qs.filter(
                order_texts__text__context__icontains=search_text
            ).distinct()

        completed_date_from = self.request.query_params.get("completed_date_from", "").strip()
        if completed_date_from:
            try:
                from_date = date_type.fromisoformat(completed_date_from)
                start = datetime_type(from_date.year, from_date.month, from_date.day, 0, 0, 0)
                if settings.USE_TZ:
                    start = tz.make_aware(start)
                qs = qs.filter(
                    Q(completed_time__gte=start) | Q(completed_time__isnull=True)
                )
            except (ValueError, TypeError):
                pass
        completed_date_to = self.request.query_params.get("completed_date_to", "").strip()
        if completed_date_to:
            try:
                to_date = date_type.fromisoformat(completed_date_to)
                end = datetime_type(
                    to_date.year, to_date.month, to_date.day, 23, 59, 59, 999999
                )
                if settings.USE_TZ:
                    end = tz.make_aware(end)
                qs = qs.filter(
                    Q(completed_time__lte=end) | Q(completed_time__isnull=True)
                )
            except (ValueError, TypeError):
                pass

        customer_id = self.request.query_params.get("customer_id")
        if customer_id not in (None, ""):
            try:
                cid = int(customer_id)
                qs = qs.filter(customer_order_field__customer_id=cid)
            except (TypeError, ValueError):
                pass

        cost_min = self.request.query_params.get("cost_min")
        if cost_min not in (None, ""):
            try:
                qs = qs.filter(cost__gte=Decimal(str(cost_min)))
            except (TypeError, ValueError):
                pass
        cost_max = self.request.query_params.get("cost_max")
        if cost_max not in (None, ""):
            try:
                qs = qs.filter(cost__lte=Decimal(str(cost_max)))
            except (TypeError, ValueError):
                pass

        price_min = self.request.query_params.get("price_min")
        if price_min not in (None, ""):
            try:
                qs = qs.filter(price__gte=Decimal(str(price_min)))
            except (TypeError, ValueError):
                pass
        price_max = self.request.query_params.get("price_max")
        if price_max not in (None, ""):
            try:
                qs = qs.filter(price__lte=Decimal(str(price_max)))
            except (TypeError, ValueError):
                pass

        profit_min = self.request.query_params.get("profit_min")
        profit_max = self.request.query_params.get("profit_max")
        if profit_min not in (None, "") or profit_max not in (None, ""):
            qs = qs.annotate(
                profit=ExpressionWrapper(
                    Coalesce(F("price"), Value(Decimal("0")))
                    - Coalesce(F("cost"), Value(Decimal("0"))),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
            if profit_min not in (None, ""):
                try:
                    qs = qs.filter(profit__gte=Decimal(str(profit_min)))
                except (TypeError, ValueError):
                    pass
            if profit_max not in (None, ""):
                try:
                    qs = qs.filter(profit__lte=Decimal(str(profit_max)))
                except (TypeError, ValueError):
                    pass

        is_completed = self.request.query_params.get("is_completed")
        if is_completed is not None:
            value = str(is_completed).lower()
            if value in ("true", "1"):
                qs = qs.filter(is_completed=True).order_by("-completed_time", "-created_at")
            elif value in ("false", "0"):
                qs = qs.filter(is_completed=False).order_by("-created_at")
        else:
            qs = qs.order_by("-created_at")

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        # 1) 校验快递单号必填 & 当前用户是否已有相同快递单号的订单
        tracking_number = (data.get("tracking_number") or "").strip()
        if not tracking_number:
            raise ValidationError({"tracking_number": "此字段为必填。"})
        if tracking_number:
            exists = Order.objects.filter(user=user, tracking_number=tracking_number).exists()
            if exists:
                # 返回 400，前端可根据 detail 提示“此快递单号已存在，请检查”
                raise ValidationError({"detail": "已有此快递单号信息"})

        # 2) 若请求中提供 order_style_id / style_id，且为当前用户的样式，则用其 style 作为订单 style
        style = serializer.validated_data.get("style") or {}
        raw_style_id = data.get("order_style_id") or data.get("style_id")
        try:
            style_id = int(raw_style_id) if raw_style_id not in (None, "",) else None
        except (TypeError, ValueError):
            style_id = None

        if style_id:
            try:
                os_obj = OrderStyle.objects.get(user=user, id=style_id)
                style = dict(os_obj.style) if os_obj.style else {}
            except OrderStyle.DoesNotExist:
                style_id = None
            except Exception:
                style_id = None

        # 3) 保存订单本身，记录创建时使用的样式 ID
        order = serializer.save(user=user, style=style, create_style_id=style_id)

        # 4) 若请求中提供 customer_id / customer-id，则自动更新 customer.CustomerOrderField
        raw_customer_id = data.get("customer_id") or data.get("customer-id")
        try:
            customer_id = int(raw_customer_id) if raw_customer_id not in (None, "",) else None
        except (TypeError, ValueError):
            customer_id = None

        if customer_id:
            try:
                from customer.models import Customer, CustomerOrderField

                customer = Customer.objects.get(user=user, id=customer_id)
                CustomerOrderField.objects.update_or_create(
                    order=order,
                    defaults={"customer": customer},
                )
            except Exception:
                # 若客户不存在或其他错误，静默忽略，不影响订单本身创建
                pass


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    查看 / 更新 / 删除当前用户的单个订单。
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_update(self, serializer):
        user = self.request.user
        data = self.request.data
        instance: Order = serializer.instance

        # 1) 处理 tracking_number：PUT 必须提供，PATCH 若提供则不能为空；同时保持用户内唯一
        method = self.request.method.upper()
        has_tn_in_data = "tracking_number" in serializer.validated_data
        if method == "PUT" or has_tn_in_data:
            new_tracking = (serializer.validated_data.get("tracking_number") or "").strip()
            if not new_tracking:
                raise ValidationError({"tracking_number": "此字段为必填。"})
            # 若修改了单号，则检查唯一性（排除当前订单本身）
            if (
                Order.objects.filter(user=user, tracking_number=new_tracking)
                .exclude(id=instance.id)
                .exists()
            ):
                raise ValidationError({"detail": "已有此快递单号信息"})
            serializer.validated_data["tracking_number"] = new_tracking

        # 2) 若请求中提供 order_style_id / style_id，且目标状态为未完成(is_completed=false)，
        #    则执行样式相关逻辑：
        #    - 若样式 ID 有效且属于当前用户，则用其 style 作为订单 style，并更新 create_style_id
        #    - 若样式 ID 显式为 null / 空，则清空 create_style_id 和 style
        style = serializer.validated_data.get("style", instance.style or {}) or {}
        create_style_id = instance.create_style_id

        raw_style_id = data.get("order_style_id") if "order_style_id" in data else data.get("style_id")
        style_id_provided = "order_style_id" in data or "style_id" in data
        try:
            style_id = int(raw_style_id) if raw_style_id not in (None, "",) else None
        except (TypeError, ValueError):
            style_id = None


        # 目标是否完成：若本次更新显式传了 is_completed，以其为准，否则沿用原值
        target_is_completed = serializer.validated_data.get("is_completed", instance.is_completed)

        if style_id_provided and not target_is_completed:
            if style_id:
                try:
                    os_obj = OrderStyle.objects.get(user=user, id=style_id)
                except Exception:
                    # 找不到或其他错误时忽略，继续使用原始 style
                    pass
                else:
                    style = os_obj.style or {}
                    create_style_id = style_id
            else:
                # 显式传入空样式 ID：清空 create_style_id，保留当前或请求中的 style
                create_style_id = None
                style = {}

        # 3) 保存订单本身
        order = serializer.save(style=style, create_style_id=create_style_id)

        # 4) 若请求中提供 customer_id / customer-id，则自动更新 customer.CustomerOrderField
        raw_customer_id = data.get("customer_id") or data.get("customer-id")
        try:
            customer_id = int(raw_customer_id) if raw_customer_id not in (None, "",) else None
        except (TypeError, ValueError):
            customer_id = None

        if customer_id:
            try:
                from customer.models import Customer, CustomerOrderField

                customer = Customer.objects.get(user=user, id=customer_id)
                CustomerOrderField.objects.update_or_create(
                    order=order,
                    defaults={"customer": customer},
                )
            except Exception:
                # 若客户不存在或其他错误，静默忽略，不影响订单本身更新
                pass


class OrderSlotUploadUrlsView(APIView):
    """
    为单个订单的某个图片槽位生成上传用预签名 URL 列表。

    - 仅允许操作当前登录用户自己的订单
    - 优先使用请求体中的 max_images；若未提供，则尝试从 Order.style.slots[slot_index].max_images 推断
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int, slot_index: int):
        user = request.user
        try:
            order = Order.objects.get(user=user, pk=pk)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 1) 解析 max_images：请求体优先，其次从订单样式中推断，最后默认 1
        raw_max_images = request.data.get("max_images", None)

        if raw_max_images in (None, ""):
            style = order.style or {}
            slots = style.get("slots") or []
            try:
                slot = slots[int(slot_index)]
            except (IndexError, TypeError, ValueError):
                slot = {}
            try:
                raw_max_images = slot.get("max_images") or 1
            except AttributeError:
                raw_max_images = 1

        try:
            max_images = int(raw_max_images)
        except (TypeError, ValueError):
            max_images = 1

        if max_images <= 0:
            max_images = 1

        # 2) 检查用户存储配额：已用空间 >= 允许空间则拒绝
        from core.models import UserPreference
        from image.services import get_user_storage_stats

        pref, _ = UserPreference.objects.get_or_create(user=user)
        limit = getattr(pref, "storage_limit_bytes", None) or (1024 * 1024 * 1024)  # 1GB
        stats = get_user_storage_stats(user.id)
        used = stats.get("total_size") or 0
        if used >= limit:
            return Response(
                {"detail": "你的空间已耗尽，请删除过时图片或联系管理员扩容权限"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3) 调用 image 服务层生成该槽位的上传 URL
        from image.services import get_order_slot_upload_presigned_urls

        data = get_order_slot_upload_presigned_urls(
            user_id=user.id,
            order_id=order.id,
            slot_index=slot_index,
            max_images=max_images,
        )
        return Response(data, status=status.HTTP_200_OK)


class OrderCompleteView(APIView):
    """
    订单发货确认：
    - 更新订单基础字段（如 cost/price/customer_id），并标记为已完成
    - 将文字内容写入 Text / OrderText
    - 根据 OSS 上实际存在的对象，为图片槽位生成 OrderImage 关联
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        user = request.user
        try:
            order = Order.objects.get(user=user, pk=pk)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload = request.data or {}
        order_data = payload.get("order") or {}
        texts_data = payload.get("texts") or []

        # 1) 更新订单基础信息
        if "cost" in order_data:
            order.cost = order_data.get("cost")
        if "price" in order_data:
            order.price = order_data.get("price")

        # 客户更新逻辑：与创建/更新订单时保持一致
        raw_customer_id = order_data.get("customer_id") if "customer_id" in order_data else None
        customer_id = None
        if raw_customer_id not in (None, ""):
            try:
                customer_id = int(raw_customer_id)
            except (TypeError, ValueError):
                customer_id = None

        from django.utils import timezone as tz

        order.is_completed = True
        order.completed_time = tz.now()
        order.save()

        if customer_id:
            try:
                from customer.models import Customer, CustomerOrderField

                customer = Customer.objects.get(user=user, id=customer_id)
                CustomerOrderField.objects.update_or_create(
                    order=order,
                    defaults={"customer": customer},
                )
            except Exception:
                # 若客户不存在或其他错误，静默忽略，不影响订单本身更新
                pass

        # 2) 写入文字内容：按槽位分组，覆盖式写入 OrderText
        style = order.style or {}
        slots = style.get("slots") or []

        texts_by_slot: dict[int, list[dict]] = {}
        if isinstance(texts_data, list):
            for item in texts_data:
                try:
                    slot_index = int(item.get("slot_index"))
                except (TypeError, ValueError):
                    continue
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                try:
                    position = int(item.get("position", 0))
                except (TypeError, ValueError):
                    position = 0
                texts_by_slot.setdefault(slot_index, []).append(
                    {"position": position, "content": content}
                )

        for slot_index, items in texts_by_slot.items():
            try:
                slot = slots[slot_index] or {}
            except (IndexError, TypeError):
                slot = {}
            key = (
                (slot.get("key") or "").strip()
                or (slot.get("name") or "").strip()
                or f"slot_{slot_index}"
            )

            # 覆盖式写入：先删再插
            OrderText.objects.filter(order=order, key=key).delete()

            # 按 position 排序后写入
            items_sorted = sorted(items, key=lambda x: x["position"])
            for item in items_sorted:
                text_obj = Text.objects.create(user=user, context=item["content"])
                OrderText.objects.create(
                    order=order,
                    text=text_obj,
                    key=key,
                    position=item["position"],
                )

        # 3) 根据 OSS 实际对象为图片槽位生成 OrderImage 关联
        from image.services import list_order_slot_objects

        bucket_default = getattr(settings, "OSS_BUCKET_NAME", "")

        for idx, raw_slot in enumerate(slots):
            slot = raw_slot or {}
            if slot.get("type") != "image":
                continue

            key = (
                (slot.get("key") or "").strip()
                or (slot.get("name") or "").strip()
                or f"slot_{idx}"
            )

            objects = list_order_slot_objects(
                user_id=user.id,
                order_id=order.id,
                slot_index=idx,
            )

            # 覆盖式写入：先删再插
            OrderImage.objects.filter(order=order, key=key).delete()

            for pos, obj in enumerate(objects):
                object_key = obj["object_key"]
                size = obj.get("size") or 0

                image, created = Image.objects.get_or_create(
                    user=user,
                    object_key=object_key,
                    defaults={
                        "bucket": bucket_default,
                        "size": size,
                    },
                )
                if not created and size and not image.size:
                    image.size = size
                    image.save(update_fields=["size"])

                OrderImage.objects.create(
                    order=order,
                    image=image,
                    key=key,
                    position=pos,
                )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderImageDeleteView(APIView):
    """删除订单下的某张图片关联（仅删除 OrderImage，不删 Image/OSS）。"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk: int, image_id: int):
        user = request.user
        try:
            order = Order.objects.get(user=user, pk=pk)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        oi = OrderImage.objects.filter(order=order, id=image_id).first()
        if not oi:
            return Response(status=status.HTTP_404_NOT_FOUND)
        oi.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderUpdateContentsView(APIView):
    """
    更新订单内容（文字 + 图片）：不改变 is_completed。
    - texts: [{ slot_index, position, content }]，覆盖式写入 OrderText
    - delete_image_ids: [OrderImage.id, ...]，删除这些订单图片关联
    - sync_images_from_oss: 若为 true，按 OSS 扫描结果重新生成图片槽位的 OrderImage
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        user = request.user
        try:
            order = Order.objects.get(user=user, pk=pk)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload = request.data or {}
        texts_data = payload.get("texts") or []
        delete_image_ids = payload.get("delete_image_ids") or []
        sync_images_from_oss = payload.get("sync_images_from_oss") is True

        style = order.style or {}
        slots = style.get("slots") or []

        # 1) 删除指定 OrderImage：同时删 OSS 对象与 Image，否则 sync_images_from_oss 会从 OSS 重新扫回被删图片
        if delete_image_ids:
            valid_ids = [int(x) for x in delete_image_ids if str(x).isdigit()]
            image_ids = set(
                OrderImage.objects.filter(order=order, id__in=valid_ids).values_list("image_id", flat=True)
            )
            from image.services import delete_image

            for image_id in image_ids:
                try:
                    delete_image(image_id)
                except Exception:
                    pass  # Image 可能已被删或 OSS 删除失败，跳过避免整批失败

        # 2) 写入文字（与 complete 相同逻辑）
        texts_by_slot = {}
        if isinstance(texts_data, list):
            for item in texts_data:
                try:
                    slot_index = int(item.get("slot_index"))
                except (TypeError, ValueError):
                    continue
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                try:
                    position = int(item.get("position", 0))
                except (TypeError, ValueError):
                    position = 0
                texts_by_slot.setdefault(slot_index, []).append(
                    {"position": position, "content": content}
                )

        for slot_index, items in texts_by_slot.items():
            try:
                slot = slots[slot_index] or {}
            except (IndexError, TypeError):
                slot = {}
            key = (
                (slot.get("key") or "").strip()
                or (slot.get("name") or "").strip()
                or f"slot_{slot_index}"
            )
            OrderText.objects.filter(order=order, key=key).delete()
            items_sorted = sorted(items, key=lambda x: x["position"])
            for item in items_sorted:
                text_obj = Text.objects.create(user=user, context=item["content"])
                OrderText.objects.create(
                    order=order,
                    text=text_obj,
                    key=key,
                    position=item["position"],
                )

        # 3) 可选：按 OSS 重新同步图片槽位
        if sync_images_from_oss:
            from image.services import list_order_slot_objects

            bucket_default = getattr(settings, "OSS_BUCKET_NAME", "")
            for idx, raw_slot in enumerate(slots):
                slot = raw_slot or {}
                if slot.get("type") != "image":
                    continue
                key = (
                    (slot.get("key") or "").strip()
                    or (slot.get("name") or "").strip()
                    or f"slot_{idx}"
                )
                objects = list_order_slot_objects(
                    user_id=user.id,
                    order_id=order.id,
                    slot_index=idx,
                )
                OrderImage.objects.filter(order=order, key=key).delete()
                for pos, obj in enumerate(objects):
                    object_key = obj["object_key"]
                    size = obj.get("size") or 0
                    image, created = Image.objects.get_or_create(
                        user=user,
                        object_key=object_key,
                        defaults={"bucket": bucket_default, "size": size},
                    )
                    if not created and size and not image.size:
                        image.size = size
                        image.save(update_fields=["size"])
                    OrderImage.objects.create(
                        order=order,
                        image=image,
                        key=key,
                        position=pos,
                    )

        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderByTrackingLookupView(APIView):
    """
    公开接口：通过 密钥 + 完整快递单号 查看只读订单（无需登录）。
    支持两种密钥：
    1) 用户密钥：UserPreference.tracking_lookup_key，匹配该用户下快递单号一致的订单；
    2) 客户密钥：Customer.tracking_lookup_key，匹配已关联该客户的订单且快递单号一致。
    GET /api/public/order-by-tracking/?key=xxx&tracking_number=yyy
    """

    permission_classes = []

    def get(self, request):
        key = (request.query_params.get("key") or "").strip()
        tracking_number = (request.query_params.get("tracking_number") or "").strip()
        if not key:
            return Response(
                {"detail": "请提供 key 参数"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not tracking_number:
            return Response(
                {"detail": "请提供 tracking_number 参数"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) 用户密钥：按用户偏好 tracking_lookup_key + 快递单号查订单
        order = (
            Order.objects.filter(
                tracking_number=tracking_number,
                user__core_user_preference__tracking_lookup_key=key,
            )
            .exclude(user__core_user_preference__tracking_lookup_key="")
            .select_related("user")
            .first()
        )

        # 2) 未命中时按客户密钥：Customer.tracking_lookup_key + 快递单号，且订单已关联该客户
        if not order:
            from customer.models import Customer

            customer = (
                Customer.objects.filter(tracking_lookup_key=key)
                .exclude(tracking_lookup_key="")
                .first()
            )
            if customer:
                order = (
                    Order.objects.filter(
                        tracking_number=tracking_number,
                        customer_order_field__customer=customer,
                    )
                    .select_related("user")
                    .first()
                )

        if not order:
            return Response(
                {"detail": "未找到对应订单或密钥/单号有误"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)


class ClearDayOrderImagesView(APIView):
    """
    清除指定完成日期的当日所有订单的图片：删除 OrderImage，并删除不再被任何订单引用的 Image（含 OSS 文件）。
    POST body: { "date": "YYYY-MM-DD" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        date_str = (request.data.get("date") or request.query_params.get("date") or "").strip()
        if not date_str:
            return Response(
                {"detail": "请提供 date 参数（YYYY-MM-DD）"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            from_date = date_type.fromisoformat(date_str)
        except (ValueError, TypeError):
            return Response(
                {"detail": "日期格式无效，请使用 YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start = datetime_type(from_date.year, from_date.month, from_date.day, 0, 0, 0)
        end = datetime_type(
            from_date.year, from_date.month, from_date.day, 23, 59, 59, 999999
        )
        if settings.USE_TZ:
            start = tz.make_aware(start)
            end = tz.make_aware(end)
        order_ids = list(
            Order.objects.filter(
                user=request.user,
                is_completed=True,
                completed_time__gte=start,
                completed_time__lte=end,
            ).values_list("id", flat=True)
        )
        # 当日订单关联的图片 ID（删除 OrderImage 前先收集）
        image_ids = set(
            OrderImage.objects.filter(order_id__in=order_ids).values_list(
                "image_id", flat=True
            )
        )
        deleted_oi, _ = OrderImage.objects.filter(order_id__in=order_ids).delete()
        # 删除后仍被其他订单引用的图片不再删除
        still_used = set(
            OrderImage.objects.filter(image_id__in=image_ids).values_list(
                "image_id", flat=True
            )
        )
        orphaned_ids = image_ids - still_used
        from image.services import delete_image

        deleted_images = 0
        for image_id in orphaned_ids:
            if not Image.objects.filter(pk=image_id, user=request.user).exists():
                continue
            try:
                delete_image(image_id)
                deleted_images += 1
            except Exception:
                pass
        return Response({"deleted_order_images": deleted_oi, "deleted_images": deleted_images})


class ClearOrderImagesView(APIView):
    """
    清除当前订单的全部图片：删除该订单下所有 OrderImage，并删除不再被任何订单引用的 Image（含 OSS 文件）。
    POST /api/orders/<pk>/clear-images/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int):
        order = Order.objects.filter(user=request.user, pk=pk).first()
        if not order:
            return Response(status=status.HTTP_404_NOT_FOUND)
        image_ids = set(
            OrderImage.objects.filter(order=order).values_list("image_id", flat=True)
        )
        deleted_oi, _ = OrderImage.objects.filter(order=order).delete()
        still_used = set(
            OrderImage.objects.filter(image_id__in=image_ids).values_list(
                "image_id", flat=True
            )
        )
        orphaned_ids = image_ids - still_used
        from image.services import delete_image

        deleted_images = 0
        for image_id in orphaned_ids:
            if not Image.objects.filter(pk=image_id, user=request.user).exists():
                continue
            try:
                delete_image(image_id)
                deleted_images += 1
            except Exception:
                pass
        return Response(
            {"deleted_order_images": deleted_oi, "deleted_images": deleted_images}
        )
