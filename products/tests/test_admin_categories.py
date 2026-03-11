from rest_framework import status
from products.models import Category, Product
from .base import AdminAPITestBase

class TestAdminCategoryAPI(AdminAPITestBase):
    def test_create_root_category(self):
        payload = {
            "slug": "electronics",
            "order": 1,
            "translations": [
                {"language": "en", "name": "Electronics"},
                {"language": "ru", "name": "Электроника"}
            ]
        }
        res = self.client.post("/api/admin/categories/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(slug="electronics")
        self.assertIsNone(cat.parent)
        self.assertEqual(cat.translations.count(), 2)
        
    def test_duplicate_slug_fails(self):
        Category.objects.create(slug="electronics")
        payload = {"slug": "electronics", "translations": [{"language": "en", "name": "E"}]}
        res = self.client.post("/api/admin/categories/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slug", res.data)

    def test_create_child_category(self):
        parent = Category.objects.create(slug="electronics")
        payload = {
            "slug": "laptops",
            "parent": parent.id,
            "translations": [{"language": "en", "name": "Laptops"}]
        }
        res = self.client.post("/api/admin/categories/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        child = Category.objects.get(slug="laptops")
        self.assertEqual(child.parent_id, parent.id)

    def test_update_category_parent(self):
        parent1 = Category.objects.create(slug="parent1")
        parent2 = Category.objects.create(slug="parent2")
        child = Category.objects.create(slug="child", parent=parent1)
        
        payload = {"parent": parent2.id}
        res = self.client.patch(f"/api/admin/categories/{child.id}/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        child.refresh_from_db()
        self.assertEqual(child.parent_id, parent2.id)

    def test_delete_empty_category(self):
        cat = Category.objects.create(slug="empty")
        res = self.client.delete(f"/api/admin/categories/{cat.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=cat.id).exists())

    def test_fail_delete_category_with_product_protect(self):
        cat = Category.objects.create(slug="protected")
        p = Product.objects.create(slug="p1", category=cat)
        
        res = self.client.delete(f"/api/admin/categories/{cat.id}/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
