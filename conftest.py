import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import (
    Category, CategoryTranslation, Brand, BrandTranslation,
    Product, ProductTranslation, ProductVariant, Tag,
)

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear Django cache between tests to avoid stale cache_response data."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="TestPass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123",
    )


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def category(db):
    cat = Category.objects.create(slug="beauty")
    CategoryTranslation.objects.create(category=cat, language="ru", name="Красота")
    return cat


@pytest.fixture
def brand(db):
    b = Brand.objects.create(slug="laneige")
    BrandTranslation.objects.create(brand=b, language="ru", name="Laneige")
    return b


@pytest.fixture
def tag(db):
    return Tag.objects.create(name="popular", slug="popular")


@pytest.fixture
def product(db, category, brand, tag):
    p = Product.objects.create(
        category=category,
        brand=brand,
        slug="test-product",
        is_active=True,
        min_price=25000,
        rating=4.5,
        review_count=10,
    )
    p.tags.add(tag)
    ProductTranslation.objects.create(
        product=p, language="ru", name="Тестовый продукт", description="Описание"
    )
    ProductVariant.objects.create(
        product=p, sku="TP-001", price=25000, old_price=30000,
        stock=10, is_active=True, is_default=True,
    )
    return p
