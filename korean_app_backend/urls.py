from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenRefreshView

from core.token_serializers import EmailTokenObtainPairSerializer
from core.custom_token_views import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.views import HealthCheckView


class PublicTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]


urlpatterns = [
    path("healthz/", HealthCheckView.as_view(), name="health_check"),
    path("admin/", admin.site.urls),
    path(
        "api/auth/login/",
        CustomTokenObtainPairView.as_view(
            serializer_class=EmailTokenObtainPairSerializer
        ),
        name="token_obtain_pair",
    ),
    path(
        "api/auth/token/refresh/",
        PublicTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/auth/", include("core.urls")),
    path("api/admin/", include("products.admin_urls")),
    path("api/v1/", include("products.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/", include("favorites.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
