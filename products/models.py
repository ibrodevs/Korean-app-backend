from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)

    class MPTTMeta:
        order_insertion_by = ["order"]

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.slug


class CategoryTranslation(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("category", "language")
        indexes = [
            models.Index(fields=["language", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"


class Brand(models.Model):
    slug = models.SlugField(unique=True, db_index=True)

    def __str__(self):
        return self.slug


class BrandTranslation(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("brand", "language")
        indexes = [
            models.Index(fields=["language", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    min_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        db_index=True,
    )
    review_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "category", "brand"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["min_price"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return self.slug


class ProductTranslation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("product", "language")
        indexes = [
            models.Index(fields=["language", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    old_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock"]),
        ]

    def __str__(self):
        return f"{self.product.slug} - {self.sku}"


class ProductImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="images",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt = models.CharField(max_length=255, null=True, blank=True)
    is_main = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        alt_text = self.alt or f"Image {self.id}"
        return f"{alt_text} (Order: {self.order})"


class Attribute(models.Model):
    VALUE_TYPE_CHOICES = [
        ("text", "Text"),
        ("int", "Integer"),
        ("float", "Float"),
        ("boolean", "Boolean"),
        ("color", "Color"),
    ]

    slug = models.SlugField(unique=True)
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES)
    is_multiple = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.slug} ({self.get_value_type_display()})"


class AttributeTranslation(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("attribute", "language")
        indexes = [
            models.Index(fields=["language", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name="values",
    )

    @property
    def typed_value(self):
        if hasattr(self, "int"):
            return self.int.value
        if hasattr(self, "float"):
            return self.float.value
        if hasattr(self, "boolean"):
            return self.boolean.value
        if hasattr(self, "color"):
            return self.color.value
        if hasattr(self, "text"):
            return self.text.value
        return None

    def __str__(self):
        value = self.typed_value
        return f"{self.attribute.slug}: {value}"


class AttributeValueTranslation(models.Model):
    value = models.ForeignKey(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("value", "language")
        indexes = [
            models.Index(fields=["language", "name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.language})"


class AttributeTextValue(models.Model):
    base = models.OneToOneField(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="text",
    )
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"Text: {self.value}"


class AttributeIntValue(models.Model):
    base = models.OneToOneField(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="int",
    )
    value = models.IntegerField(db_index=True)

    def __str__(self):
        return f"Int: {self.value}"


class AttributeFloatValue(models.Model):
    base = models.OneToOneField(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="float",
    )
    value = models.FloatField(db_index=True)

    def __str__(self):
        return f"Float: {self.value}"


class AttributeBooleanValue(models.Model):
    base = models.OneToOneField(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="boolean",
    )
    value = models.BooleanField(db_index=True)

    def __str__(self):
        return f"Boolean: {self.value}"


class AttributeColorValue(models.Model):
    base = models.OneToOneField(
        AttributeValue,
        on_delete=models.CASCADE,
        related_name="color",
    )
    value = models.CharField(max_length=7, db_index=True)

    def __str__(self):
        return f"Color: {self.value}"


class ProductVariantAttribute(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="single_attributes",
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("variant", "attribute")
        indexes = [
            models.Index(fields=["variant", "attribute"]),
        ]

    def __str__(self):
        return f"{self.variant} - {self.attribute}: {self.value}"


class ProductVariantMultiAttribute(models.Model):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="multi_attributes",
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("variant", "attribute", "value")
        indexes = [
            models.Index(fields=["variant", "attribute"]),
        ]

    def __str__(self):
        return f"{self.variant} - {self.attribute}: {self.value}"



