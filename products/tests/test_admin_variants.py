from rest_framework import status
from products.models import Product, Category, ProductVariant, Attribute, AttributeValue
from .base import AdminAPITestBase
from decimal import Decimal

class TestAdminVariantAPI(AdminAPITestBase):
    def setUp(self):
        super().setUp()
        self.cat = Category.objects.create(slug="cat")
        self.product = Product.objects.create(slug="p1", category=self.cat)

    def test_crud_variant(self):
        payload = {
            "sku": "V-1",
            "price": "100.00",
            "stock": 10
        }
        # Create
        res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        variant_id = res.data["id"]
        
        # Read list
        res = self.client.get(f"/api/admin/products/{self.product.id}/variants/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        
        # Patch
        res = self.client.patch(f"/api/admin/variants/{variant_id}/", {"price": "150.00"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Delete
        res = self.client.delete(f"/api/admin/variants/{variant_id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_duplicate_sku_fails(self):
        ProductVariant.objects.create(product=self.product, sku="DUPE", price=10)
        payload = {"sku": "DUPE", "price": "20.00"}
        res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_stock_or_price_fails(self):
        # Depending on models it might raise error or pass. PRD says: price >= 0, stock >= 0
        payload = {"sku": "BAD", "price": "-10.00", "stock": -5}
        res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_one_default_variant(self):
        # Creating first variant should make it default
        v1_res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", {"sku": "V1", "price": "10", "is_default": True}, format="json")
        v1 = ProductVariant.objects.get(id=v1_res.data["id"])
        self.assertTrue(v1.is_default)
        
        # Creating second variant as default should unset the first one
        v2_res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", {"sku": "V2", "price": "10", "is_default": True}, format="json")
        v2 = ProductVariant.objects.get(id=v2_res.data["id"])
        
        v1.refresh_from_db()
        self.assertFalse(v1.is_default)
        self.assertTrue(v2.is_default)

    def test_multi_attribute_logic(self):
        attr = Attribute.objects.create(slug="features", value_type="text", is_multiple=True)
        v = ProductVariant.objects.create(product=self.product, sku="v-multi", price=100)
        
        payload = [
            {"attribute": "features", "value": "waterproof"},
            {"attribute": "features", "value": "bluetooth"}
        ]
        res = self.client.post(f"/api/admin/variants/{v.id}/attributes/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.assertEqual(v.multi_attributes.count(), 2)
        vals = [ma.value.typed_value for ma in v.multi_attributes.all()]
        self.assertIn("waterproof", vals)
        self.assertIn("bluetooth", vals)

    def test_single_attribute_logic(self):
        attr = Attribute.objects.create(slug="color", value_type="text", is_multiple=False)
        v = ProductVariant.objects.create(product=self.product, sku="v-single", price=100)
        
        payload = {"attribute": "color", "value": "red"}
        res = self.client.post(f"/api/admin/variants/{v.id}/attribute/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.assertEqual(v.single_attributes.count(), 1)
        self.assertEqual(v.single_attributes.first().value.typed_value, "red")

    def test_min_price_auto_update_on_variant_price_change(self):
        # Initial variant creates min price
        res1 = self.client.post(f"/api/admin/products/{self.product.id}/variants/", {"sku": "V-MIN-1", "price": "100.00"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.min_price, Decimal("100.00"))
        
        # Cheaper variant lowers min price
        res2 = self.client.post(f"/api/admin/products/{self.product.id}/variants/", {"sku": "V-MIN-2", "price": "50.00"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.min_price, Decimal("50.00"))
        
        # Updating the second variant raises the min price back up
        self.client.patch(f"/api/admin/variants/{res2.data['id']}/", {"price": "150.00"}, format="json")
        self.product.refresh_from_db()
        self.assertEqual(self.product.min_price, Decimal("100.00"))
        
        # Deleting the cheapest variant removes it and recalculates min price
        self.client.delete(f"/api/admin/variants/{res1.data['id']}/")
        self.product.refresh_from_db()
        self.assertEqual(self.product.min_price, Decimal("150.00"))

    def test_nested_variant_create_rejects_multiple_values_for_single_attribute(self):
        # We must explicitly create the single-value Color attribute to hit the logic error
        Attribute.objects.create(slug="color", value_type="text", is_multiple=False)
        payload = {
            "sku": "v-multi-fail-2",
            "price": "100",
            "attributes": [
                {"attribute": "color", "value": "red"},
                {"attribute": "color", "value": "blue"}
            ]
        }
        res = self.client.post(f"/api/admin/products/{self.product.id}/variants/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assign multiple values", str(res.data[0]))

