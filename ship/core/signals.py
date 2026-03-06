from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserPreference


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_preference_on_user_create(sender, instance, created, **kwargs):
    """
    新建用户时自动创建一条 UserPreference 记录。
    button_reverse 字段在模型中已设置 default=False，
    因此此处无需显式赋值，保持默认即可。
    """
    if not created:
        return

    # 若已存在则不重复创建（防御性检查）
    UserPreference.objects.get_or_create(user=instance)

