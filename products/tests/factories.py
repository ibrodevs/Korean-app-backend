import factory
from decimal import Decimal

from products.models import (
    Category,
    CategoryTranslation,
    Brand,
    BrandTranslation,
    Product,
    ProductTranslation,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
    AttributeTextValue,
    AttributeIntValue,
    AttributeColorValue,
    ProductVariantAttribute,
    ProductVariantMultiAttribute,
)


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    slug = factory.Sequence(lambda n: f"category-{n}")
    order = factory.Sequence(lambda n: n)


class CategoryTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CategoryTranslation
        django_get_or_create = ("category", "language")

    category = factory.SubFactory(CategoryFactory)
    language = "ru"
    name = factory.LazyAttribute(lambda o: f"Категория {o.category.slug}")


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Brand

    slug = factory.Sequence(lambda n: f"brand-{n}")


class BrandTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BrandTranslation
        django_get_or_create = ("brand", "language")

    brand = factory.SubFactory(BrandFactory)
    language = "ru"
    name = factory.LazyAttribute(lambda o: f"Бренд {o.brand.slug}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    brand = factory.SubFactory(BrandFactory)
    slug = factory.Sequence(lambda n: f"product-{n}")
    is_active = True
    min_price = Decimal("100.00")


class ProductTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductTranslation
        django_get_or_create = ("product", "language")

    product = factory.SubFactory(ProductFactory)
    language = "ru"
    name = factory.LazyAttribute(lambda o: f"Товар {o.product.slug}")
    description = factory.LazyAttribute(lambda o: f"Описание {o.product.slug}")
    meta_title = ""
    meta_description = ""
    meta_keywords = ""


class ProductVariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductVariant

    product = factory.SubFactory(ProductFactory)
    sku = factory.Sequence(lambda n: f"SKU-{n:06d}")
    price = Decimal("100.00")
    old_price = None
    stock = 10
    is_active = True
    is_default = True


class ProductImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    variant = None
    image = factory.django.ImageField(filename="test.jpg")
    alt = "test image"
    is_main = True
    order = 0


class AttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Attribute

    slug = factory.Sequence(lambda n: f"attr-{n}")
    value_type = "text"
    is_multiple = False


class AttributeTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeTranslation
        django_get_or_create = ("attribute", "language")

    attribute = factory.SubFactory(AttributeFactory)
    language = "ru"
    name = factory.LazyAttribute(lambda o: f"Атрибут {o.attribute.slug}")


class AttributeValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeValue

    attribute = factory.SubFactory(AttributeFactory)


class AttributeValueTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeValueTranslation
        django_get_or_create = ("value", "language")

    value = factory.SubFactory(AttributeValueFactory)
    language = "ru"
    name = factory.Faker("word")


class AttributeTextValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeTextValue

    base = factory.SubFactory(AttributeValueFactory)
    value = factory.Faker("word")


class AttributeIntValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeIntValue

    base = factory.SubFactory(AttributeValueFactory)
    value = 8


class AttributeColorValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeColorValue

    base = factory.SubFactory(AttributeValueFactory)
    value = "#FF0000"


class ProductVariantAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductVariantAttribute

    variant = factory.SubFactory(ProductVariantFactory)
    attribute = factory.SubFactory(AttributeFactory)
    value = factory.SubFactory(AttributeValueFactory)


class ProductVariantMultiAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductVariantMultiAttribute

    variant = factory.SubFactory(ProductVariantFactory)
    attribute = factory.SubFactory(AttributeFactory)
    value = factory.SubFactory(AttributeValueFactory)
