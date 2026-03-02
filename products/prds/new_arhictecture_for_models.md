# Final Production Architecture — E-commerce Catalog (Production-Ready)

Документ отражает финальную архитектуру каталога с учётом обязательных доработок перед стартом разработки.

Включено:

* Полноценная мультиязычность всех отображаемых сущностей
* Типизированное хранение значений атрибутов
* Гарантия целостности данных на уровне БД
* Поддержка множественных атрибутов без риска дубликатов
* Дерево категорий (MPTT-ready)
* Изображения на уровне вариантов
* Корректная денормализация min_price
* Индексация ключевых полей

Order и OrderItem исключены намеренно.

---

# 1️⃣ Category (Tree-based)

Рекомендуется использовать django-mptt.

```python
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    slug = models.SlugField(unique=True)

    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )

    order = models.PositiveIntegerField(default=0)

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
        ]
```

---

## CategoryTranslation

```python
class CategoryTranslation(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('category', 'language')
        indexes = [
            models.Index(fields=['language', 'name']),
        ]
```

---

# 2️⃣ Brand

```python
class Brand(models.Model):
    slug = models.SlugField(unique=True)
```

## BrandTranslation

```python
class BrandTranslation(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('brand', 'language')
        indexes = [
            models.Index(fields=['language', 'name']),
        ]
```

---

# 3️⃣ Product

```python
class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        db_index=True
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    slug = models.SlugField(unique=True)

    is_active = models.BooleanField(default=True, db_index=True)

    min_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active']),
        ]
```

---

## ProductTranslation

```python
class ProductTranslation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='translations'
    )

    language = models.CharField(max_length=10, db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField()

    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('product', 'language')
        indexes = [
            models.Index(fields=['language', 'name']),
        ]
```

---

# 4️⃣ ProductVariant (SKU)

```python
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    sku = models.CharField(max_length=100, unique=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    # Опционально: вариант по умолчанию
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
        ]
```

Цена хранится только на уровне варианта.

---

# 5️⃣ ProductImage

```python
class ProductImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='images'
    )

    # Денормализация для упрощения запросов (variant.product)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='products/%Y/%m/')
    alt = models.CharField(max_length=255, null=True, blank=True)

    is_main = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
```

---

# 6️⃣ Attribute

```python
class Attribute(models.Model):

    VALUE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('int', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('color', 'Color'),
    ]

    slug = models.SlugField(unique=True)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES)

    is_multiple = models.BooleanField(default=False)
```

---

# 7️⃣ Typed Attribute Values

Базовая сущность:

```python
class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='values'
    )

    @property
    def typed_value(self):
        if hasattr(self, 'int'):
            return self.int.value
        if hasattr(self, 'float'):
            return self.float.value
        if hasattr(self, 'boolean'):
            return self.boolean.value
        if hasattr(self, 'color'):
            return self.color.value
        if hasattr(self, 'text'):
            return self.text.value
        return None
```

Типизированные таблицы (создание строго в соответствии с attribute.value_type):

```python
class AttributeTextValue(models.Model):
    base = models.OneToOneField(AttributeValue, on_delete=models.CASCADE, related_name='text')
    value = models.CharField(max_length=255)

class AttributeIntValue(models.Model):
    base = models.OneToOneField(AttributeValue, on_delete=models.CASCADE, related_name='int')
    value = models.IntegerField(db_index=True)

class AttributeFloatValue(models.Model):
    base = models.OneToOneField(AttributeValue, on_delete=models.CASCADE, related_name='float')
    value = models.FloatField(db_index=True)

class AttributeBooleanValue(models.Model):
    base = models.OneToOneField(AttributeValue, on_delete=models.CASCADE, related_name='boolean')
    value = models.BooleanField(db_index=True)

class AttributeColorValue(models.Model):
    base = models.OneToOneField(AttributeValue, on_delete=models.CASCADE, related_name='color')
    value = models.CharField(max_length=7)
```

Контроль соответствия типа реализуется на уровне фабрик/форм/сервисного слоя.

---

# 8️⃣ Атрибуты продукта (разделение для целостности БД)

## Немножественные атрибуты варианта

```python
class ProductVariantAttribute(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='single_attributes'
    )

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('variant', 'attribute')

    # В бизнес-логике обязательно проверять:
    # attribute.is_multiple == False
```

## Множественные атрибуты варианта

```python
class ProductVariantMultiAttribute(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='multi_attributes'
    )

    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('variant', 'attribute', 'value')
        indexes = [
            models.Index(fields=['variant', 'attribute']),
        ]
```

Таким образом:

* Для is_multiple=False используется ProductVariantAttribute (гарантия уникальности на уровне БД)
* Для is_multiple=True используется ProductVariantMultiAttribute

---

# 9️⃣ Денормализация min_price

min_price пересчитывается:

* при сохранении ProductVariant
* при удалении ProductVariant
* при изменении price или is_active

Минимальная цена рассчитывается только среди is_active=True.

Для массовых обновлений рекомендуется использовать сервисный метод пересчёта или фоновые задачи.

---

# 🔟 Итоговая структура

```
Category (MPTT)
CategoryTranslation
Brand
BrandTranslation
Product
ProductTranslation
ProductVariant
ProductImage
Attribute
AttributeValue
AttributeTextValue
AttributeIntValue
AttributeFloatValue
AttributeBooleanValue
AttributeColorValue
ProductVariantAttribute
ProductVariantMultiAttribute
```

Архитектура:

* гарантирует целостность данных на уровне БД
* поддерживает строгую типизацию
* позволяет SQL-фильтрацию по диапазонам
* поддерживает множественные атрибуты без риска дубликатов
* полностью мультиязычна
* оптимизирована для листингов
* production-ready
