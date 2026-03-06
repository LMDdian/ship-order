from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "核心"

    def ready(self) -> None:
        # 导入信号处理器，以便在应用加载时注册 post_save 钩子
        from . import signals  # noqa: F401

        return super().ready()
