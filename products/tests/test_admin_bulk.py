from rest_framework import status
from products.models import Product, Category, ProductVariant
from .base import AdminAPITestBase
from decimal import Decimal

class TestAdminBulkOperationsAPI(AdminAPITestBase):
    def setUp(self):
        super().setUp()
        self.cat = Category.objects.create(slug="cat")
        self.product = Product.objects.create(slug="p1", category=self.cat)
        self.v1 = ProductVariant.objects.create(product=self.product, sku="v1", price=100, stock=10)
        self.v2 = ProductVariant.objects.create(product=self.product, sku="v2", price=200, stock=20)

    def test_bulk_price_success(self):
        payload = {
            "variants": [
                {"id": self.v1.id, "price": "150.00"},
                {"id": self.v2.id, "price": "250.00"}
            ]
        }
        res = self.client.patch("/api/admin/variants/bulk-price/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.v1.refresh_from_db()
        self.v2.refresh_from_db()
        self.assertEqual(self.v1.price, Decimal("150.00"))
        self.assertEqual(self.v2.price, Decimal("250.00"))

    def test_bulk_stock_success(self):
        payload = {
            "variants": [
                {"id": self.v1.id, "stock": 15},
                {"id": self.v2.id, "stock": 25}
            ]
        }
        res = self.client.patch("/api/admin/variants/bulk-stock/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.v1.refresh_from_db()
        self.v2.refresh_from_db()
        self.assertEqual(self.v1.stock, 15)
        self.assertEqual(self.v2.stock, 25)

    def test_bulk_price_partial_invalid_payload_atomicity(self):
        # We test that if one item fails validation, none are updated.
        payload = {
            "variants": [
                {"id": self.v1.id, "price": "150.00"},
                {"id": self.v2.id, "price": "-250.00"} # negative price should fail
            ]
        }
        res = self.client.patch("/api/admin/variants/bulk-price/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify atomicity - v1 should remain at 100, not jump to 150
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.price, Decimal("100.00"))

    def test_bulk_invalid_ids(self):
        payload = {
            "variants": [
                {"id": 9999, "stock": 15}
            ]
        }
        res = self.client.patch("/api/admin/variants/bulk-stock/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
