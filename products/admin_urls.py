from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .admin_views import (
    AdminCategoryViewSet,
    AdminBrandViewSet,
    AdminProductViewSet,
    AdminProductVariantViewSet,
    AdminProductImageViewSet,
    AdminAttributeViewSet,
    AdminAttributeValueViewSet,
)

router = DefaultRouter()
router.register(r"categories", AdminCategoryViewSet, basename="admin-category")
router.register(r"brands", AdminBrandViewSet, basename="admin-brand")
router.register(r"products", AdminProductViewSet, basename="admin-product")
router.register(r"variants", AdminProductVariantViewSet, basename="admin-variant")
router.register(r"images", AdminProductImageViewSet, basename="admin-image")
router.register(r"attributes", AdminAttributeViewSet, basename="admin-attribute")
router.register(r"attribute-values", AdminAttributeValueViewSet, basename="admin-attribute-value")

urlpatterns = [
    path("", include(router.urls)),
]
