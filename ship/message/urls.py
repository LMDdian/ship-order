from django.urls import path

from .views import MessageDetailView, MessageListView, MessageUnreadCountView

urlpatterns = [
    path("", MessageListView.as_view(), name="message-list"),
    path("unread-count/", MessageUnreadCountView.as_view(), name="message-unread-count"),
    path("<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
]
