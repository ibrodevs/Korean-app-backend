from rest_framework import status
from products.models import Attribute, AttributeValue
from .base import AdminAPITestBase

class TestAdminAttributeAPI(AdminAPITestBase):
    def test_text_attribute_creation(self):
        payload = {
            "slug": "color",
            "value_type": "text",
            "translations": [{"language": "en", "name": "Color"}]
        }
        res = self.client.post("/api/admin/attributes/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        attr = Attribute.objects.get(slug="color")
        self.assertEqual(attr.value_type, "text")

    def test_typed_attribute_value_creation(self):
        attr = Attribute.objects.create(slug="size", value_type="int")
        payload = {
            "attribute": attr.id,
            "value": "42",
            "translations": [{"language": "en", "name": "Size 42"}]
        }
        res = self.client.post("/api/admin/attribute-values/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        val = AttributeValue.objects.get(id=res.data["id"])
        self.assertEqual(val.typed_value, 42)
        # Verify it stored in int table
        self.assertTrue(hasattr(val, "int"))
        self.assertEqual(val.int.value, 42)

    def test_color_attribute_value_creation(self):
        attr = Attribute.objects.create(slug="hexcolor", value_type="color")
        payload = {
            "attribute": attr.id,
            "value": "#FF0000",
            "translations": []
        }
        res = self.client.post("/api/admin/attribute-values/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        val = AttributeValue.objects.get(id=res.data["id"])
        self.assertEqual(val.typed_value, "#FF0000")
        
    def test_boolean_attribute_value_creation(self):
        attr = Attribute.objects.create(slug="is_smart", value_type="boolean")
        payload = {
            "attribute": attr.id,
            "value": "true",
            "translations": []
        }
        res = self.client.post("/api/admin/attribute-values/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        val = AttributeValue.objects.get(id=res.data["id"])
        self.assertEqual(val.typed_value, True)

    def test_float_attribute_value_creation(self):
        attr = Attribute.objects.create(slug="weight", value_type="float")
        payload = {
            "attribute": attr.id,
            "value": "1.5",
            "translations": []
        }
        res = self.client.post("/api/admin/attribute-values/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        val = AttributeValue.objects.get(id=res.data["id"])
        self.assertEqual(val.typed_value, 1.5)

    def test_invalid_type_fails(self):
        attr = Attribute.objects.create(slug="bad_int", value_type="int")
        payload = {
            "attribute": attr.id,
            "value": "not_a_number",
            "translations": []
        }
        res = self.client.post("/api/admin/attribute-values/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_attribute_value_type_immutable(self):
        attr = Attribute.objects.create(slug="test", value_type="text")
        res = self.client.patch(f"/api/admin/attributes/{attr.id}/", {"value_type": "int"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        attr.refresh_from_db()
        self.assertEqual(attr.value_type, "text") # should ignore the change

    def test_strict_color_validation(self):
        attr = Attribute.objects.create(slug="color_strict", value_type="color")
        
        # Bad color 1
        res1 = self.client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": "red"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Bad color 2
        res2 = self.client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": "123456"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Bad color 3
        res3 = self.client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": "#GGGGGG"}, format="json")
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_strict_boolean_validation(self):
        attr = Attribute.objects.create(slug="bool_strict", value_type="boolean")
        
        # Bad bool 1
        res1 = self.client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": "maybe"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Valid bool formats
        for val in ["true", "false", "True", "False", "1", "0", True, False]:
            res = self.client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": val}, format="json")
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
