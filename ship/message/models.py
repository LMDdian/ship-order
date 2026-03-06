from django.conf import settings
from django.db import models


class Message(models.Model):
    """发给用户的消息"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_messages",
        verbose_name="用户",
    )
    title = models.CharField("标题", max_length=256)
    content = models.TextField("内容", blank=True)
    looked = models.BooleanField("已读", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_message"
        verbose_name = "消息"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message({self.user_id}, {self.title[:20]}…)"
