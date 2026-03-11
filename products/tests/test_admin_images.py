import tempfile
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from products.models import Product, Category, ProductVariant, ProductImage
from .base import AdminAPITestBase

class TestAdminImageAPI(AdminAPITestBase):
    def setUp(self):
        super().setUp()
        self.cat = Category.objects.create(slug="cat")
        self.product = Product.objects.create(slug="p1", category=self.cat)
        self.variant = ProductVariant.objects.create(product=self.product, sku="v1", price=100)

    def generate_image(self):
        image = PILImage.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        return SimpleUploadedFile(tmp_file.name, tmp_file.read(), content_type='image/jpeg')

    def test_upload_image_to_product(self):
        payload = {
            "image": self.generate_image(),
            "alt": "product image",
            "is_main": True,
            "order": 1
        }
        # Note: According to PRD, Endpoint is /admin/products/{id}/images
        res = self.client.post(f"/api/admin/products/{self.product.id}/images/", payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.product.images.count(), 1)
        self.assertTrue(self.product.images.first().is_main)

    def test_only_one_main_image(self):
        img1 = ProductImage.objects.create(product=self.product, is_main=True, alt="1")
        
        payload = {
            "image": self.generate_image(),
            "is_main": True
        }
        res = self.client.post(f"/api/admin/products/{self.product.id}/images/", payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        img1.refresh_from_db()
        self.assertFalse(img1.is_main)
        
        new_img = ProductImage.objects.get(id=res.data["id"])
        self.assertTrue(new_img.is_main)

    def test_upload_image_to_variant(self):
        payload = {
            "image": self.generate_image(),
            "alt": "variant image"
        }
        res = self.client.post(f"/api/admin/variants/{self.variant.id}/images/", payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.variant.images.count(), 1)
        # Note: Should still be associated with the product inherently because Image model requires product.
        self.assertEqual(self.variant.images.first().product_id, self.product.id)
