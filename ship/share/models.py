import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ShareLink(models.Model):
    """订单分享链接：token 唯一，过期后不可访问"""

    order = models.ForeignKey(
        "core.Order",
        on_delete=models.CASCADE,
        related_name="share_links",
        verbose_name="订单",
    )
    token = models.CharField("分享令牌", max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField("过期时间")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_share_link"
        verbose_name = "分享链接"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Share({self.order_id}, {self.token[:8]}…)"

    @classmethod
    def generate_token(cls):
        return uuid.uuid4().hex

    def is_expired(self):
        return timezone.now() >= self.expires_at
