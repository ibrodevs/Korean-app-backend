import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "korean_app_backend.settings")
django.setup()

from rest_framework.test import APIClient
from products.models import Attribute, AttributeValue
from core.models import CustomUser

client = APIClient()
user = CustomUser.objects.create_superuser('admin@fail.com', 'pass')
client.force_authenticate(user=user)

attr = Attribute.objects.create(slug="bool_strict_debug", value_type="boolean")
for val in ["true", "false", "True", "False", "1", "0", True, False]:
    res = client.post("/api/admin/attribute-values/", {"attribute": attr.id, "value": val}, format="json")
    print(f"VAL {val} -> STATUS {res.status_code}")
    if res.status_code != 201:
        print(f"Response: {res.data}")
