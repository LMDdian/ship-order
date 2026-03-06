from rest_framework import serializers

from core.models import OrderStyle, UserPreference


class OrderStyleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStyle
        fields = ["id", "name"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    default_order_style = OrderStyleBriefSerializer(read_only=True)
    default_order_style_id = serializers.PrimaryKeyRelatedField(
        source="default_order_style",
        queryset=OrderStyle.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    storage_used_bytes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserPreference
        fields = [
            "id",
            "button_reverse",
            "default_order_style",
            "default_order_style_id",
            "tracking_lookup_key",
            "storage_limit_bytes",
            "storage_used_bytes",
        ]
        read_only_fields = ["id", "default_order_style", "storage_used_bytes"]

    def get_storage_used_bytes(self, obj):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None):
            return 0
        try:
            from image.services import get_user_storage_stats
            return get_user_storage_stats(request.user.id).get("total_size") or 0
        except Exception:
            return 0

