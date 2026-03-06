from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    # 推荐使用 simplejwt 来发放 JWT
    from rest_framework_simplejwt.tokens import RefreshToken
except Exception as exc:  # pragma: no cover - 运行时如未安装 simplejwt，会在启动阶段暴露
    RefreshToken = None  # type: ignore[assignment]


class LoginView(APIView):
    """
    简单登录接口：
    - 接收 username / password
    - 校验通过后返回 JWT（access / refresh）和精简的 user 信息
    - user 中包含 id / username / first_name / last_name
    """

    permission_classes: list = []
    authentication_classes: list = []

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "username 和 password 必填"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "用户名或密码错误"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 如果项目中已安装 simplejwt，则正常发放 JWT；否则只返回用户信息
        access = refresh = None
        if RefreshToken is not None:
            refresh_obj = RefreshToken.for_user(user)
            refresh = str(refresh_obj)
            access = str(refresh_obj.access_token)

        return Response(
            {
                "access": access,
                "refresh": refresh,
                "user": {
                    "id": user.id,
                    "username": user.get_username(),
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )

