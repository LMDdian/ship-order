from rest_framework import generics, permissions

from .models import Customer
from .serializers import CustomerSerializer


class CustomerListView(generics.ListCreateAPIView):
    """当前登录用户的客户列表 + 新建"""

    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """单个客户的获取 / 更新 / 删除"""

    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)
