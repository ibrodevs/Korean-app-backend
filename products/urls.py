from django.urls import path

from .views import (
    ProductListAPIView,
    ProductDetailAPIView,
    CatalogSearchAPIView,
    CategoryTreeAPIView,
    BrandListAPIView,
)


urlpatterns = [
    path("products/", ProductListAPIView.as_view(), name="products-list"),
    path(
        "products/<slug:slug>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    path(
        "catalog-search/",
        CatalogSearchAPIView.as_view(),
        name="catalog-search",
    ),
    path(
        "categories/",
        CategoryTreeAPIView.as_view(),
        name="categories-tree",
    ),
    path(
        "brands/",
        BrandListAPIView.as_view(),
        name="brands-list",
    ),
]

