from rest_framework import generics, permissions, response, status

from core.models import OrderStyle
from .serializers import OrderStyleSerializer
from .services import get_order_style_for_user


class OrderStyleListCreateView(generics.ListCreateAPIView):
    """
    当前登录用户的 OrderStyle 列表 + 新建。
    """

    serializer_class = OrderStyleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return OrderStyle.objects.filter(user=user).order_by("-updated_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderStyleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    查看 / 更新 / 删除当前用户的单个 OrderStyle。
    """

    serializer_class = OrderStyleSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        user = self.request.user
        return OrderStyle.objects.filter(user=user).order_by("-updated_at")


class OrderStyleStyleView(generics.GenericAPIView):
    """
    仅返回 style JSON 的轻量接口，方便前端或其他 app 使用。
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int, *args, **kwargs):
        style = get_order_style_for_user(request.user, pk)
        return response.Response(style.style or {}, status=status.HTTP_200_OK)

