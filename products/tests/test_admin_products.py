from rest_framework import status
from decimal import Decimal
from products.models import Product, Category, Brand, ProductTranslation
from .base import AdminAPITestBase

class TestAdminProductAPI(AdminAPITestBase):
    def setUp(self):
        super().setUp()
        self.cat = Category.objects.create(slug="cat")
        self.brand = Brand.objects.create(slug="brand")

    def test_list_products(self):
        Product.objects.create(slug="p1", category=self.cat)
        res = self.client.get("/api/admin/products/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        count = res.data.get("count", len(res.data))
        self.assertEqual(count, Product.objects.count())

    def test_detail_product(self):
        p = Product.objects.create(slug="p1", category=self.cat)
        ProductTranslation.objects.create(product=p, language="en", name="Test")
        res = self.client.get(f"/api/admin/products/{p.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["slug"], "p1")
        self.assertEqual(res.data["translations"][0]["name"], "Test")

    def test_patch_product(self):
        p = Product.objects.create(slug="p1", category=self.cat)
        res = self.client.patch(f"/api/admin/products/{p.id}/", {"is_active": False}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        p.refresh_from_db()
        self.assertFalse(p.is_active)

    def test_delete_product(self):
        p = Product.objects.create(slug="p1", category=self.cat)
        res = self.client.delete(f"/api/admin/products/{p.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=p.id).exists())

    def test_duplicate_slug_fails(self):
        Product.objects.create(slug="p1", category=self.cat)
        payload = {
            "slug": "p1",
            "category": self.cat.id
        }
        res = self.client.post("/api/admin/products/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slug", res.data)

    def test_missing_required_fields_fails(self):
        payload = {
            "slug": "p1"
            # missing category
        }
        res = self.client.post("/api/admin/products/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", res.data)

    def test_duplicate_translation_language(self):
        payload = {
            "slug": "p2",
            "category": self.cat.id,
            "translations": [
                {"language": "en", "name": "Name 1", "description": "Desc 1"},
                {"language": "en", "name": "Name 2", "description": "Desc 2"}
            ]
        }
        res = self.client.post("/api/admin/products/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("language already exists", str(res.data).lower())
    def test_update_translation(self):
        p = Product.objects.create(slug="p1", category=self.cat)
        # Create via API to test update
        self.client.patch(f"/api/admin/products/{p.id}/", {"translations": [{"language": "en", "name": "Old"}]}, format="json")
        
        # Now update
        res = self.client.patch(f"/api/admin/products/{p.id}/", {"translations": [{"language": "en", "name": "New"}]}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        p.refresh_from_db()
        self.assertEqual(p.translations.count(), 1)
        self.assertEqual(p.translations.first().name, "New")

    def test_list_products_with_filters_and_pagination(self):
        cat2 = Category.objects.create(slug="cat2")
        brand2 = Brand.objects.create(slug="brand2")
        
        Product.objects.create(slug="p1", category=self.cat, brand=self.brand, min_price=10)
        Product.objects.create(slug="p2", category=self.cat, brand=brand2, min_price=50)
        Product.objects.create(slug="p3", category=cat2, brand=self.brand, min_price=100)
        Product.objects.create(slug="p4", category=cat2, brand=brand2, min_price=150)
        
        # Test pagination
        res = self.client.get("/api/admin/products/?limit=2&offset=2")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)
        self.assertEqual(res.data["count"], 4)
        
        # Test filter by category
        res = self.client.get(f"/api/admin/products/?category={self.cat.slug}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should be p1, p2
        self.assertEqual(res.data["count"], 2)
        slugs = sorted([p["slug"] for p in res.data["results"]])
        self.assertEqual(slugs, ["p1", "p2"])
        
        # Test filter by price_min
        res = self.client.get("/api/admin/products/?price_min=100")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should be p3, p4
        self.assertEqual(res.data["count"], 2)
        slugs = sorted([p["slug"] for p in res.data["results"]])
        self.assertEqual(slugs, ["p3", "p4"])
        
        # Test filter by brand and max_price
        res = self.client.get(f"/api/admin/products/?brand={self.brand.slug}&price_max=50")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Should be just p1
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["slug"], "p1")

    def test_bulk_product_creation(self):
        payload = [
            {
                "slug": "bulk-product-1",
                "category": self.cat.id,
                "brand": self.brand.id,
                "translations": [
                    {
                        "language": "en",
                        "name": "Bulk Product 1",
                        "description": "Desc 1"
                    }
                ],
                "variants": [
                    {"sku": "BP1-V1", "price": "10.00", "stock": 5}
                ]
            },
            {
                "slug": "bulk-product-2",
                "category": self.cat.id,
                "brand": self.brand.id,
                "translations": [
                    {
                        "language": "en",
                        "name": "Bulk Product 2",
                        "description": "Desc 2"
                    }
                ],
                "variants": [
                    {"sku": "BP2-V1", "price": "20.00", "stock": 10}
                ]
            }
        ]
        
        res = self.client.post("/api/admin/products/bulk/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(res.data), 2)
        
        # Verify db records
        self.assertTrue(Product.objects.filter(slug="bulk-product-1").exists())
        self.assertTrue(Product.objects.filter(slug="bulk-product-2").exists())
        
        # Verify min_price is calculated
        p = Product.objects.get(slug="bulk-product-2")
        self.assertEqual(p.min_price, Decimal("20.00"))

