from django.urls import path

from .views import OrderStyleDetailView, OrderStyleListCreateView, OrderStyleStyleView

urlpatterns = [
    path("", OrderStyleListCreateView.as_view(), name="orderstyle-list"),
    path("<int:pk>/", OrderStyleDetailView.as_view(), name="orderstyle-detail"),
    path("<int:pk>/style/", OrderStyleStyleView.as_view(), name="orderstyle-style"),
]

