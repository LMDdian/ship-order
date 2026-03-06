from django.urls import path

from .views import (
    ShareLinkDetailView,
    ShareLinkListCreateView,
    ShareLinkRevokeView,
)

urlpatterns = [
    path("", ShareLinkListCreateView.as_view(), name="share-list-create"),
    path("revoke/<int:pk>/", ShareLinkRevokeView.as_view(), name="share-revoke"),
    path("<str:token>/", ShareLinkDetailView.as_view(), name="share-detail"),
]
