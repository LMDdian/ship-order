from rest_framework import serializers

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    # 只读：若订单有关联客户，则返回客户名称和客户 ID，否则为 null
    customer_name = serializers.SerializerMethodField(read_only=True)
    customer_id = serializers.SerializerMethodField(read_only=True)
    # 卡片展示用：首图 URL、前两条文字（按槽位顺序），便于已完成订单列表/瀑布流展示
    card_image_url = serializers.SerializerMethodField(read_only=True)
    card_line1 = serializers.SerializerMethodField(read_only=True)
    card_line2 = serializers.SerializerMethodField(read_only=True)
    # 该订单下所有图片占用空间（字节）
    image_storage_bytes = serializers.SerializerMethodField(read_only=True)
    # 详情页用：按槽位返回当前文字/图片内容，仅 Retrieve 时包含
    slot_contents = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "style",
            "create_style_id",
            "cost",
            "price",
            "is_completed",
            "completed_time",
            "customer_id",
            "customer_name",
            "card_image_url",
            "card_line1",
            "card_line2",
            "image_storage_bytes",
            "slot_contents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "customer_id",
            "customer_name",
            "card_image_url",
            "card_line1",
            "card_line2",
            "image_storage_bytes",
            "slot_contents",
        ]

    def _get_customer_relation(self, obj: Order):
        try:
            return obj.customer_order_field  # related_name
        except Exception:
            return None

    def get_customer_name(self, obj: Order):
        cof = self._get_customer_relation(obj)
        if not cof:
            return None
        customer = getattr(cof, "customer", None)
        return getattr(customer, "name", None)

    def get_customer_id(self, obj: Order):
        cof = self._get_customer_relation(obj)
        if not cof:
            return None
        customer = getattr(cof, "customer", None)
        return getattr(customer, "id", None)

    def get_card_image_url(self, obj: Order):
        """已完成订单卡片首图：取第一个 OrderImage 的预签名下载 URL。"""
        first_oi = (
            obj.order_images.select_related("image")
            .order_by("key", "position", "id")
            .first()
        )
        if not first_oi or not getattr(first_oi, "image", None):
            return None
        try:
            from image.services import get_presigned_url

            result = get_presigned_url(first_oi.image_id, expires_minutes=60)
            return result.get("url")
        except Exception:
            return None

    def get_card_line1(self, obj: Order):
        """卡片第一行文字：按 key、position 排序后的第一条 OrderText 的 content。"""
        first_ot = (
            obj.order_texts.select_related("text")
            .order_by("key", "position", "id")
            .first()
        )
        if not first_ot or not getattr(first_ot, "text", None):
            return None
        return getattr(first_ot.text, "context", None) or ""

    def get_card_line2(self, obj: Order):
        """卡片第二行文字：按 key、position 排序后的第二条 OrderText 的 content。"""
        two = list(
            obj.order_texts.select_related("text")
            .order_by("key", "position", "id")[:2]
        )
        if len(two) < 2:
            return None
        second_ot = two[1]
        if not getattr(second_ot, "text", None):
            return None
        return getattr(second_ot.text, "context", None) or ""

    def get_image_storage_bytes(self, obj: Order):
        """该订单下所有关联图片的 size 之和（字节）。"""
        from django.db.models import Sum

        total = (
            obj.order_images.select_related("image")
            .aggregate(total=Sum("image__size"))["total"]
        )
        return total if total is not None else 0

    def get_slot_contents(self, obj: Order):
        """
        仅当为 Retrieve 请求时返回；按 style.slots 顺序返回每槽位的当前内容：
        - type, name, slot_index
        - text 槽位: text 为第一条 OrderText 的 content
        - image 槽位: images 为 [{ id: OrderImage.id, url: 预签名 }]
        """
        request = self.context.get("request")
        if not request or request.method != "GET":
            return None
        style = obj.style or {}
        slots = style.get("slots") or []
        if not slots:
            return []
        result = []
        for idx, raw_slot in enumerate(slots):
            slot = raw_slot or {}
            slot_type = "image" if slot.get("type") == "image" else "text"
            key = (
                (slot.get("key") or "").strip()
                or (slot.get("name") or "").strip()
                or f"slot_{idx}"
            )
            entry = {
                "slot_index": idx,
                "type": slot_type,
                "name": slot.get("name") or f"槽位{idx + 1}",
            }
            if slot_type == "text":
                first_ot = (
                    obj.order_texts.filter(key=key)
                    .select_related("text")
                    .order_by("position", "id")
                    .first()
                )
                entry["text"] = ""
                if first_ot and getattr(first_ot, "text", None):
                    entry["text"] = getattr(first_ot.text, "context", None) or ""
            else:
                images = (
                    obj.order_images.filter(key=key)
                    .select_related("image")
                    .order_by("position", "id")
                )
                urls = []
                for oi in images:
                    if not getattr(oi, "image", None):
                        continue
                    try:
                        from image.services import get_presigned_url
                        res = get_presigned_url(oi.image_id, expires_minutes=60)
                        url = res.get("url")
                        if url:
                            urls.append({"id": oi.id, "url": url})
                    except Exception:
                        pass
                entry["images"] = urls
            result.append(entry)
        return result

