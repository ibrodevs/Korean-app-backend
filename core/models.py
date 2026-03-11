from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from products.models import ProductVariant
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        creates and returns user
        """

        if not email:
            raise ValueError('Пользователь должен иметь email адрес')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # Allow users without password (OAuth users)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """creates and returns superuser"""

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):
    """
    Docstring for User
    """
    # OAuth provider choices
    AUTH_PROVIDER_EMAIL = 'email'
    AUTH_PROVIDER_GOOGLE = 'google'
    AUTH_PROVIDER_CHOICES = [
        (AUTH_PROVIDER_EMAIL, 'Email'),
        (AUTH_PROVIDER_GOOGLE, 'Google'),
    ]

    username = None
    email = models.EmailField(('email address'), unique=True, db_index=True)
    phone = models.CharField(max_length=120, blank=True, null=True)
    
    # OAuth fields
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDER_CHOICES,
        default=AUTH_PROVIDER_EMAIL
    )

    photo = models.ImageField(null=True, blank=True, verbose_name='profile photo')


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name='user'
        verbose_name_plural='users'



class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "variant"], name="unique_cart_variant")
        ]
        indexes = [
            models.Index(fields=["cart", "variant"]),
        ]

    def __str__(self):
        return f"{self.variant.sku} x {self.quantity}"

    @property
    def total_price(self):
        return self.variant.price * self.quantity