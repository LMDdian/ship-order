from rest_framework import generics, permissions

from core.models import UserPreference
from .serializers import UserPreferenceSerializer


class MeUserPreferenceView(generics.RetrieveUpdateAPIView):
    """
    当前登录用户的 UserPreference：
    - GET /api/user-preference/  获取当前用户偏好
    - PUT/PATCH /api/user-preference/  更新当前用户偏好（如默认订单样式、按钮偏好）
    """

    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> UserPreference:
        # UserPreference 在 core.signals 中已经在用户创建时自动建立；若意外不存在，get_or_create 防御性补建
        pref, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return pref

