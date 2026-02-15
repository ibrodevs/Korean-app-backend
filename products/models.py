from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import ContentType


class Product(models.Model):
    """Базовая модель товара"""
    name_ru = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)
    name_kg = models.CharField(max_length=255)
    description_ru = models.CharField(max_length=500, verbose_name='description in russian', null=True, blank=True)
    description_kg = models.CharField(max_length=500, verbose_name='description in kyrgyz', null=True, blank=True)
    description_en = models.CharField(max_length=500, verbose_name='description in english', null=True, blank=True)

    discount = models.IntegerField(verbose_name='discount', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name='product'
        verbose_name_plural='products'
        abstract = True

    def get_name(self, lang='ru'):
        return getattr(self, f'name_{lang}', self.name_ru)
    
    def get_description(self, lang='ru'):
        return getattr(self, f'description_{lang}', self.description_ru)

    def __str__(self):
        return self.name_ru or self.name_en

class WomenClothes(Product):
    """Женская одежда"""
    SIZE_CHOICES = [
        ('xs', 'XS'), ('s', 'S'), ('m', 'M'), ('l', 'L'), 
        ('xl', 'XL'), ('xxl', 'XXL'), ('3xl', '3XL')
    ]
    COLOR_CHOICES = [
        ('white', 'Белый'), ('black', 'Черный'), ('grey', 'Серый'),
        ('blue', 'Синий'), ('red', 'Красный'), ('green', 'Зеленый'),
        ('yellow', 'Желтый'), ('pink', 'Розовый'), ('beige', 'Бежевый'),
        ('brown', 'Коричневый'), ('purple', 'Фиолетовый'), ('multicolor', 'Мультицвет')
    ]
    MATERIAL_CHOICES = [
        ('cotton', 'Хлопок'), ('wool', 'Шерсть'), ('linen', 'Лен'),
        ('silk', 'Шелк'), ('viscose', 'Вискоза'), ('polyester', 'Полиэстер'),
        ('leather', 'Кожа'), ('denim', 'Джинс'), ('spandex', 'Спандекс')
    ]
    SEASON_CHOICES = [
        ('summer', 'Лето'), ('winter', 'Зима'), ('autumn', 'Осень'),
        ('spring', 'Весна'), ('allseason', 'Всесезон')
    ]
    
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)
    brand = models.CharField(max_length=100, null=True, blank=True)


class MenClothes(Product):
    """Мужская одежда"""
    SIZE_CHOICES = [
        ('xs', 'XS'), ('s', 'S'), ('m', 'M'), ('l', 'L'), 
        ('xl', 'XL'), ('xxl', 'XXL'), ('3xl', '3XL')
    ]
    COLOR_CHOICES = [
        ('white', 'Белый'), ('black', 'Черный'), ('grey', 'Серый'),
        ('blue', 'Синий'), ('red', 'Красный'), ('green', 'Зеленый'),
        ('yellow', 'Желтый'), ('brown', 'Коричневый'), ('beige', 'Бежевый'),
        ('multicolor', 'Мультицвет')
    ]
    MATERIAL_CHOICES = [
        ('cotton', 'Хлопок'), ('wool', 'Шерсть'), ('linen', 'Лен'),
        ('polyester', 'Полиэстер'), ('denim', 'Джинс'), ('leather', 'Кожа'), 
        ('spandex', 'Спандекс')
    ]
    STYLE_CHOICES = [
        ('straight', 'Прямой'), ('fitted', 'Приталенный'), ('loose', 'Свободный'),
        ('sports', 'Спортивный'), ('classic', 'Классический'), ('casual', 'Повседневный')
    ]
    
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES)
    style = models.CharField(max_length=20, choices=STYLE_CHOICES)
    brand = models.CharField(max_length=100, null=True, blank=True)


class KidsClothes(Product):
    """Детская одежда"""
    AGE_CHOICES = [
        ('0-6m', '0–6 месяцев'), ('6-12m', '6–12 месяцев'), ('1-2y', '1–2 года'),
        ('3-5y', '3–5 лет'), ('6-8y', '6–8 лет'), ('9-12y', '9–12 лет'),
        ('13-16y', '13–16 лет')
    ]
    GENDER_CHOICES = [
        ('boy', 'Мальчик'), ('girl', 'Девочка'), ('unisex', 'Унисекс')
    ]
    COLOR_CHOICES = [
        ('white', 'Белый'), ('black', 'Черный'), ('blue', 'Синий'),
        ('red', 'Красный'), ('pink', 'Розовый'), ('green', 'Зеленый'),
        ('yellow', 'Желтый'), ('multicolor', 'Мультицвет')
    ]
    MATERIAL_CHOICES = [
        ('cotton', 'Хлопок'), ('linen', 'Лен'), ('polyester', 'Полиэстер'),
        ('denim', 'Джинс'), ('wool', 'Шерсть'), ('viscose', 'Вискоза')
    ]
    
    age_group = models.CharField(max_length=10, choices=AGE_CHOICES)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES)


class Shoes(Product):
    """Обувь"""
    SIZE_CHOICES = [(str(i), str(i)) for i in range(18, 47)]
    COLOR_CHOICES = [
        ('black', 'Черный'), ('white', 'Белый'), ('grey', 'Серый'),
        ('blue', 'Синий'), ('red', 'Красный'), ('brown', 'Коричневый'),
        ('beige', 'Бежевый'), ('green', 'Зеленый'), ('pink', 'Розовый'),
        ('multicolor', 'Мультицвет')
    ]
    MATERIAL_CHOICES = [
        ('leather', 'Кожа'), ('faux_leather', 'Искусственная кожа'),
        ('suede', 'Замша'), ('textile', 'Текстиль'), ('rubber', 'Резина')
    ]
    SEASON_CHOICES = [
        ('summer', 'Лето'), ('winter', 'Зима'), ('autumn', 'Осень'),
        ('spring', 'Весна'), ('allseason', 'Всесезон')
    ]
    
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)
    brand = models.CharField(max_length=100, null=True, blank=True)



class Accessories(Product):
    """Аксессуары и сумки"""
    TYPE_CHOICES = [
        ('bag', 'Сумка'), ('backpack', 'Рюкзак'), ('wallet', 'Кошелек'),
        ('belt', 'Ремень'), ('watches', 'Часы'), ('eyewear', 'Очки'),
        ('scarves', 'Шарфы'), ('gloves', 'Перчатки'),
    ]
    MATERIAL_CHOICES = [
        ('leather', 'Кожа'), ('textile', 'Текстиль'), ('plastic', 'Пластик'),
        ('metal', 'Металл'), ('suede', 'Замша'), ('synthetic', 'Синтетика'),
    ]

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)


class Beauty(Product):
    """Красота и здоровье"""
    PRODUCT_TYPE = [
        ('face', 'Уход за лицом'), ('body', 'Уход за телом'), ('hair', 'Волосы'),
        ('makeup', 'Макияж'), ('perfume', 'Парфюмерия'), ('vitamins', 'Витамины'),
        ('medical', 'Медтехника'),
    ]
    PURPOSE_CHOICES = [
        ('moisturize', 'Увлажнение'), ('nutrition', 'Питание'), ('anti_age', 'Омоложение'),
        ('protection', 'Защита'), ('treatment', 'Лечение'),
    ]
    SHELF_LIFE_CHOICES = [
        ('<6m', 'до 6 мес'), ('6-12m', '6–12 мес'), ('12-24m', '12–24 мес'), ('>24m', 'более 24 мес')
    ]

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, null=True, blank=True)
    ingredients = models.CharField(max_length=255, null=True, blank=True)
    volume = models.CharField(max_length=50, null=True, blank=True)
    shelf_life = models.CharField(max_length=10, choices=SHELF_LIFE_CHOICES, null=True, blank=True)


class HomeProduct(Product):
    """Дом и интерьер"""
    ITEM_CHOICES = [
        ('furniture', 'Мебель'), ('lighting', 'Освещение'), ('decor', 'Декор'),
        ('textile', 'Текстиль'), ('kitchen', 'Кухонная посуда'), ('storage', 'Хранение')
    ]
    MATERIAL_CHOICES = [
        ('wood', 'Дерево'), ('metal', 'Металл'), ('plastic', 'Пластик'), ('textile', 'Текстиль'),
        ('glass', 'Стекло'), ('ceramic', 'Керамика')
    ]

    item_type = models.CharField(max_length=20, choices=ITEM_CHOICES)
    material = models.CharField(max_length=20, choices=MATERIAL_CHOICES, null=True, blank=True)
    dimensions = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=30, null=True, blank=True)


class Electronics(Product):
    """Электроника и гаджеты"""
    CONDITION_CHOICES = [
        ('new', 'Новый'), ('used', 'Б/у')
    ]

    brand = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    ram = models.CharField(max_length=50, null=True, blank=True)
    storage = models.CharField(max_length=50, null=True, blank=True)
    processor = models.CharField(max_length=100, null=True, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='new')
    warranty_months = models.PositiveIntegerField(null=True, blank=True)


class SportsProduct(Product):
    """Спорт и отдых"""
    SPORT_CHOICES = [
        ('football', 'Футбол'), ('basketball', 'Баскетбол'), ('yoga', 'Йога'),
        ('fitness', 'Фитнес'), ('cycling', 'Велоспорт'), ('hiking', 'Туризм'),
        ('swimming', 'Плавание'), ('running', 'Бег')
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Начинающий'), ('intermediate', 'Средний'), ('advanced', 'Продвинутый'), ('pro', 'Профи')
    ]

    sport_type = models.CharField(max_length=20, choices=SPORT_CHOICES)
    size = models.CharField(max_length=10, null=True, blank=True)
    material = models.CharField(max_length=50, null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)





class Order(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Заказано'),
        ('in_transit', 'В пути'),
        ('delivered', 'Доставлено')
    ]

    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # Поля для GenericForeignKey
    product_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['shoes', 'WomenClothes', 'MenClothes', 'KidClothes', 'Accessories', 'Beauty', 'HomeProduct', 'Electronics', 'SportsProduct']}  # можно ограничить модели
    )
    product_object_id = models.PositiveIntegerField()
    product = GenericForeignKey('product_content_type', 'product_object_id')
    
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['order', 'product_content_type', 'product_object_id']





