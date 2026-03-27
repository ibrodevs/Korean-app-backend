import json

import pytest
from products.models import Product, ProductVariant, ProductTranslation


def get_data(resp):
    """Get response data from either DRF Response or Django HttpResponse."""
    if hasattr(resp, 'data'):
        return resp.data
    return json.loads(resp.content)


@pytest.mark.django_db
class TestProductList:
    def test_list_returns_200(self, api_client, product):
        resp = api_client.get("/api/v1/products/")
        assert resp.status_code == 200

    def test_list_contains_required_fields(self, api_client, product):
        resp = api_client.get("/api/v1/products/")
        assert resp.status_code == 200
        results = get_data(resp)["results"]
        assert len(results) > 0
        item = results[0]
        for field in ("id", "name", "slug", "price", "old_price", "is_sale",
                      "is_new", "rating", "review_count", "stock_status", "tags", "image"):
            assert field in item, f"Missing field: {field}"

    def test_list_pagination(self, api_client, product):
        resp = api_client.get("/api/v1/products/")
        assert "count" in get_data(resp)
        assert "results" in get_data(resp)

    def test_list_accessible_without_auth(self, api_client, product):
        resp = api_client.get("/api/v1/products/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestProductDetail:
    def test_detail_returns_200(self, api_client, product):
        resp = api_client.get(f"/api/v1/products/{product.slug}/")
        assert resp.status_code == 200

    def test_detail_contains_required_fields(self, api_client, product):
        resp = api_client.get(f"/api/v1/products/{product.slug}/")
        for field in ("id", "name", "slug", "price", "old_price", "is_sale",
                      "is_new", "rating", "review_count", "stock_status", "tags"):
            assert field in get_data(resp), f"Missing field: {field}"

    def test_detail_not_found(self, api_client):
        resp = api_client.get("/api/v1/products/non-existent-slug/")
        assert resp.status_code == 404

    def test_detail_accessible_without_auth(self, api_client, product):
        resp = api_client.get(f"/api/v1/products/{product.slug}/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestProductFilters:
    def test_filter_sale_only(self, api_client, product):
        # product fixture has old_price=30000 > price=25000 → is_sale=True
        resp = api_client.get("/api/v1/products/?sale_only=true")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_sale_only_excludes_non_sale(self, api_client, category, brand):
        # product without old_price
        p = Product.objects.create(
            category=category, brand=brand,
            slug="no-sale-product", is_active=True, min_price=10000,
        )
        ProductTranslation.objects.create(
            product=p, language="ru", name="No Sale", description=""
        )
        ProductVariant.objects.create(
            product=p, sku="NS-001", price=10000, stock=5,
            is_active=True, is_default=True,
        )
        resp = api_client.get("/api/v1/products/?sale_only=true")
        slugs = [r["slug"] for r in get_data(resp)["results"]]
        assert "no-sale-product" not in slugs

    def test_filter_in_stock_only(self, api_client, product):
        resp = api_client.get("/api/v1/products/?in_stock_only=true")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_rating_min(self, api_client, product):
        resp = api_client.get("/api/v1/products/?rating_min=4.0")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_rating_min_excludes(self, api_client, product):
        resp = api_client.get("/api/v1/products/?rating_min=5.0")
        assert resp.status_code == 200
        # product has rating=4.5, so should be excluded
        assert get_data(resp)["count"] == 0

    def test_filter_tags(self, api_client, product):
        resp = api_client.get("/api/v1/products/?tags=popular")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_category(self, api_client, product):
        resp = api_client.get("/api/v1/products/?category=beauty")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_min_price(self, api_client, product):
        resp = api_client.get("/api/v1/products/?price_min=20000")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1

    def test_filter_max_price(self, api_client, product):
        resp = api_client.get("/api/v1/products/?price_max=10000")
        assert resp.status_code == 200
        assert get_data(resp)["count"] == 0

    def test_search(self, api_client, product):
        resp = api_client.get("/api/v1/products/?search=Тестовый")
        assert resp.status_code == 200
        assert get_data(resp)["count"] >= 1


@pytest.mark.django_db
class TestStockStatus:
    def test_in_stock(self, api_client, product):
        # product fixture has stock=10
        resp = api_client.get(f"/api/v1/products/{product.slug}/")
        assert get_data(resp)["stock_status"] == "in_stock"

    def test_low_stock(self, api_client, category, brand):
        p = Product.objects.create(
            category=category, brand=brand,
            slug="low-stock", is_active=True, min_price=5000,
        )
        ProductTranslation.objects.create(
            product=p, language="ru", name="Low Stock", description=""
        )
        ProductVariant.objects.create(
            product=p, sku="LS-001", price=5000, stock=3,
            is_active=True, is_default=True,
        )
        resp = api_client.get(f"/api/v1/products/{p.slug}/")
        assert get_data(resp)["stock_status"] == "low_stock"

    def test_out_of_stock(self, api_client, category, brand):
        p = Product.objects.create(
            category=category, brand=brand,
            slug="out-of-stock", is_active=True, min_price=5000,
        )
        ProductTranslation.objects.create(
            product=p, language="ru", name="Out of Stock", description=""
        )
        ProductVariant.objects.create(
            product=p, sku="OOS-001", price=5000, stock=0,
            is_active=True, is_default=True,
        )
        resp = api_client.get(f"/api/v1/products/{p.slug}/")
        assert get_data(resp)["stock_status"] == "out_of_stock"


@pytest.mark.django_db
class TestIsSale:
    def test_is_sale_true(self, api_client, product):
        # product fixture: old_price=30000 > price=25000
        resp = api_client.get(f"/api/v1/products/{product.slug}/")
        assert get_data(resp)["is_sale"] is True

    def test_is_sale_false(self, api_client, category, brand):
        p = Product.objects.create(
            category=category, brand=brand,
            slug="no-sale", is_active=True, min_price=10000,
        )
        ProductTranslation.objects.create(
            product=p, language="ru", name="No Sale", description=""
        )
        ProductVariant.objects.create(
            product=p, sku="NS-002", price=10000, stock=5,
            is_active=True, is_default=True,
        )
        resp = api_client.get(f"/api/v1/products/{p.slug}/")
        assert get_data(resp)["is_sale"] is False
