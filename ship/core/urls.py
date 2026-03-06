from django.urls import path

from .views import (
    ClearDayOrderImagesView,
    ClearOrderImagesView,
    OrderByTrackingLookupView,
    OrderCompleteView,
    OrderDetailView,
    OrderImageDeleteView,
    OrderListCreateView,
    OrderSlotUploadUrlsView,
    OrderUpdateContentsView,
)

urlpatterns = [
    path(
        "public/order-by-tracking/",
        OrderByTrackingLookupView.as_view(),
        name="public-order-by-tracking",
    ),
    path("orders/", OrderListCreateView.as_view(), name="order-list"),
    path(
        "orders/clear-day-images/",
        ClearDayOrderImagesView.as_view(),
        name="order-clear-day-images",
    ),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<int:pk>/clear-images/",
        ClearOrderImagesView.as_view(),
        name="order-clear-images",
    ),
    path(
        "orders/<int:pk>/slots/<int:slot_index>/upload-urls/",
        OrderSlotUploadUrlsView.as_view(),
        name="order-slot-upload-urls",
    ),
    path(
        "orders/<int:pk>/complete/",
        OrderCompleteView.as_view(),
        name="order-complete",
    ),
    path(
        "orders/<int:pk>/images/<int:image_id>/",
        OrderImageDeleteView.as_view(),
        name="order-image-delete",
    ),
    path(
        "orders/<int:pk>/update-contents/",
        OrderUpdateContentsView.as_view(),
        name="order-update-contents",
    ),
]

