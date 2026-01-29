from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        creates and returns user
        """

        if not email:
            raise ValueError('Пользователь должен иметь email адрес')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
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
    username = None
    email = models.EmailField(('email address'), unique=True)

    gender = models.BooleanField(null=True, blank=True, verbose_name='True= women, false=men')
    birth_date = models.DateField(null=True, blank=True, verbose_name='birth_day')
    photo = models.ImageField(null=True, blank=True, verbose_name='profile photo')


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name='user'
        verbose_name_plural='users'

    
