from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework_simplejwt.views import TokenRefreshView

from core.api_auth import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/login/", LoginView.as_view(), name="api-login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("core.urls")),
    path("api/order-styles/", include("orderstyle.urls")),
    path("api/processing/", include("processing.urls")),
    path("api/user-preference/", include("preference.urls")),
    path("api/customers/", include("customer.urls")),
    path("api/share/", include("share.urls")),
    path("api/messages/", include("message.urls")),
]

# 试运行：提供 Vue 打包后的静态资源（/assets/...）
frontend_dist = getattr(settings, "FRONTEND_DIST", None)
if frontend_dist and frontend_dist.exists():
    assets_root = frontend_dist / "assets"
    urlpatterns += [
        re_path(r"^assets/(?P<path>.*)$", serve, {"document_root": assets_root}),
        re_path(r"^.*$", lambda r: HttpResponse((frontend_dist / "index.html").read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")),
    ]

if settings.DEBUG and getattr(settings, "MEDIA_ROOT", None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
