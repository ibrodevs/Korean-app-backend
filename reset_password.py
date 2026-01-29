import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'korean_app_backend.settings')
django.setup()

from core.models import CustomUser
user = CustomUser.objects.get(email='AdilhanSatymkulov40@gmail.com')
user.set_password('Adil2008!')
user.save()
print('Password reset successfully for:', user.email)
