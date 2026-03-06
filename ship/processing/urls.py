from django.urls import path

from .views import ProcessingFieldListView, ProcessingListView

urlpatterns = [
    # 默认返回 ProcessingField 列表（含关联的 Processing），供前端选择 processing 配置
    path("", ProcessingFieldListView.as_view(), name="processing-field-list"),
    # 如需仅查看 Processing 类型本身，可访问 /api/processing/types/
    path("types/", ProcessingListView.as_view(), name="processing-list"),
]

