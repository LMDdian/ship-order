from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "title", "content", "looked", "created_at"]
        read_only_fields = ["id", "title", "content", "created_at"]
