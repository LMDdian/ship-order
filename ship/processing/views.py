from rest_framework import generics, permissions

from core.models import Processing, ProcessingField
from .serializers import ProcessingFieldSerializer, ProcessingSerializer


class ProcessingListView(generics.ListAPIView):
    """
    列出所有 Processing 处理模型（如「缩略图」「水印」等），供前端下拉选择。
    """

    queryset = Processing.objects.all().order_by("id")
    serializer_class = ProcessingSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProcessingFieldListView(generics.ListAPIView):
    """
    列出所有 ProcessingField 配置项，包含其关联的 Processing。
    通常前端只需要 id + processing.name 即可。
    """

    queryset = ProcessingField.objects.select_related("processing").all().order_by("id")
    serializer_class = ProcessingFieldSerializer
    permission_classes = [permissions.IsAuthenticated]

