from django.urls import path

from .views import MeUserPreferenceView

urlpatterns = [
    path("", MeUserPreferenceView.as_view(), name="user-preference-me"),
]

