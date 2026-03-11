from rest_framework import status
from products.models import Brand, Product, Category
from .base import AdminAPITestBase

class TestAdminBrandAPI(AdminAPITestBase):
    def test_crud_brand(self):
        # Create
        payload = {
            "slug": "nike",
            "translations": [
                {"language": "en", "name": "Nike"},
                {"language": "ru", "name": "Найк"}
            ]
        }
        res = self.client.post("/api/admin/brands/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        brand_id = res.data["id"]
        
        # Read
        res = self.client.get(f"/api/admin/brands/{brand_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["slug"], "nike")
        self.assertEqual(len(res.data["translations"]), 2)
        
        # Update translation
        payload = {
            "translations": [
                {"language": "ru", "name": "Найки"}
            ]
        }
        res = self.client.patch(f"/api/admin/brands/{brand_id}/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        brand = Brand.objects.get(id=brand_id)
        
        self.assertEqual(brand.translations.count(), 2)
        ru_translation = brand.translations.get(language="ru")
        self.assertEqual(ru_translation.name, "Найки")
    def test_delete_brand_sets_null_on_product(self):
        cat = Category.objects.create(slug="cat")
        brand = Brand.objects.create(slug="nike")
        product = Product.objects.create(slug="p1", category=cat, brand=brand)
        
        res = self.client.delete(f"/api/admin/brands/{brand.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        
        product.refresh_from_db()
        self.assertIsNone(product.brand)
        
    def test_duplicate_brand_slug(self):
        Brand.objects.create(slug="nike")
        res = self.client.post("/api/admin/brands/", {"slug": "nike"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
