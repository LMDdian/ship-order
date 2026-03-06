from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "looked", "created_at"]
    list_filter = ["looked", "created_at"]
    search_fields = ["title", "content", "user__username"]
