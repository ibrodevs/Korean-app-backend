from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.test import override_settings

User = get_user_model()

@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    ELASTICSEARCH_DSL_AUTOSYNC=False
)
class AdminAPITestBase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin@example.com", "password")
        self.standard_user = User.objects.create_user("user@example.com", "password")
        self.client.force_authenticate(user=self.admin_user)
