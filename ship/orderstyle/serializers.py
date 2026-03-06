from typing import Any, Dict, List

from rest_framework import serializers

from core.models import OrderStyle


class OrderStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStyle
        fields = ["id", "name", "description", "style", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def _normalize_slots(self, slots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为缺失的 key / order 自动生成默认值。"""
        normalized: List[Dict[str, Any]] = []
        for idx, raw in enumerate(slots):
            slot = dict(raw or {})
            # order：按当前顺序生成
            slot.setdefault("order", idx)
            # key：如果未提供，则自动生成 slot_1, slot_2 ...
            if not slot.get("key"):
                slot["key"] = f"slot_{idx + 1}"
            normalized.append(slot)
        return normalized

    def validate_style(self, value: Dict[str, Any]) -> Dict[str, Any]:
        value = value or {}
        slots = value.get("slots")
        if isinstance(slots, list):
            value["slots"] = self._normalize_slots(slots)
        return value

