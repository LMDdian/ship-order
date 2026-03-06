from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from core.models import OrderStyle

User = get_user_model()


def get_order_style_for_user(user: User, style_id: int) -> OrderStyle:
    """
    获取当前用户可访问的 OrderStyle，若不存在或不属于该用户则抛出 PermissionDenied。
    供其他 app 在服务层直接调用。
    """
    try:
        style = OrderStyle.objects.get(pk=style_id)
    except OrderStyle.DoesNotExist as exc:  # pragma: no cover - 简单包装
        raise PermissionDenied("样式不存在") from exc

    if style.user_id != user.id:
        raise PermissionDenied("无权访问该样式")
    return style


def get_style_payload_for_user(user: User, style_id: int) -> Dict[str, Any]:
    """
    返回给前端 / 其他服务使用的 style JSON。
    若无权访问会抛出 PermissionDenied。
    """
    style = get_order_style_for_user(user, style_id)
    return style.style or {}

