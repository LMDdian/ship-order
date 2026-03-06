from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Order
from core.serializers import OrderSerializer
from .models import ShareLink


def _share_link_payload(link: ShareLink):
    base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
    path = f"/share/{link.token}"
    share_url = f"{base_url}{path}" if base_url else path
    return {
        "id": link.id,
        "order_id": link.order_id,
        "tracking_number": link.order.tracking_number or "",
        "token": link.token,
        "share_url": share_url,
        "expires_at": link.expires_at.isoformat(),
        "created_at": link.created_at.isoformat(),
        "is_expired": link.is_expired(),
    }


class ShareLinkListCreateView(APIView):
    """
    当前用户的分享链接：GET 列表，POST 创建。
    GET /api/share/
    POST /api/share/ body: { "order_id": int, "expires_minutes": int }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = (
            ShareLink.objects.filter(order__user=request.user)
            .select_related("order")
            .order_by("-created_at")
        )
        return Response([_share_link_payload(link) for link in links])

    def post(self, request):
        order_id = request.data.get("order_id")
        expires_minutes = request.data.get("expires_minutes", 60)
        try:
            order_id = int(order_id)
            expires_minutes = int(expires_minutes)
        except (TypeError, ValueError):
            return Response(
                {"detail": "order_id 与 expires_minutes 须为整数"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if expires_minutes < 1 or expires_minutes > 10080:  # 最多 7 天
            return Response(
                {"detail": "expires_minutes 须在 1～10080（7天）之间"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        expires_at = timezone.now() + timedelta(minutes=expires_minutes)
        token = ShareLink.generate_token()
        ShareLink.objects.create(order=order, token=token, expires_at=expires_at)

        base_url = getattr(settings, "FRONTEND_BASE_URL", "").rstrip("/")
        path = f"/share/{token}"
        share_url = f"{base_url}{path}" if base_url else path

        return Response(
            {
                "share_url": share_url,
                "expires_at": expires_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class ShareLinkDetailView(APIView):
    """
    通过 token 获取分享的订单详情（无需登录，过期不可访问）。
    GET /api/share/<token>/
    """

    permission_classes = []

    def get(self, request, token: str):
        link = ShareLink.objects.filter(token=token).select_related("order").first()
        if not link:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if link.is_expired():
            return Response(
                {"detail": "分享链接已过期"},
                status=status.HTTP_410_GONE,
            )
        order = link.order
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)


class ShareLinkRevokeView(APIView):
    """
    撤销（删除）分享链接（需登录，仅能删自己的）。
    DELETE /api/share/<pk>/
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk: int):
        link = ShareLink.objects.filter(pk=pk, order__user=request.user).first()
        if not link:
            return Response(status=status.HTTP_404_NOT_FOUND)
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
