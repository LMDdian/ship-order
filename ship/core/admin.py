from django.contrib import admin
from .models import (
    Processing,
    ProcessingField,
    Image,
    Text,
    Order,
    OrderImage,
    OrderText,
    OrderStyle,
    Share,
    SharePermission,
)


@admin.register(Processing)
class ProcessingAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(ProcessingField)
class ProcessingFieldAdmin(admin.ModelAdmin):
    list_display = ["id", "processing"]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "bucket", "object_key", "size", "created_at"]
    list_filter = ["bucket"]


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "context_preview", "created_at"]

    def context_preview(self, obj):
        return (obj.context[:50] + "…") if obj.context and len(obj.context) > 50 else (obj.context or "-")

    context_preview.short_description = "内容"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "tracking_number", "created_at", "updated_at"]
    list_filter = ["user"]


@admin.register(OrderImage)
class OrderImageAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "key", "image", "position"]


@admin.register(OrderText)
class OrderTextAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "key", "text", "position"]


@admin.register(OrderStyle)
class OrderStyleAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "name", "updated_at"]


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "creator", "expires_at", "created_at"]


@admin.register(SharePermission)
class SharePermissionAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "creator", "token", "expires_at", "created_at"]
