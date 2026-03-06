from rest_framework import serializers

from core.models import Processing, ProcessingField


class ProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processing
        fields = ["id", "name"]


class ProcessingFieldSerializer(serializers.ModelSerializer):
    processing = ProcessingSerializer(read_only=True)

    class Meta:
        model = ProcessingField
        fields = ["id", "processing"]

