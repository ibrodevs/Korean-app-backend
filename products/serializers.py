from rest_framework import serializers

from .models import (
    Category,
    CategoryTranslation,
    Brand,
    BrandTranslation,
    Product,
    ProductTranslation,
    ProductVariant,
    ProductImage,
    Attribute,
    AttributeValue,
    AttributeValueTranslation,
    ProductVariantAttribute,
    ProductVariantMultiAttribute,
)


class TranslationMixin:
    """
    Helper mixin to pick a translation for the requested language.
    """

    def _get_language(self) -> str:
        return self.context.get("language", "ru")

    def _get_translation(self, translations, language_field: str = "language"):
        lang = self._get_language()
        by_lang = {t.language: t for t in translations}
        return by_lang.get(lang) or by_lang.get("ru")


class CategorySerializer(TranslationMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "slug", "parent", "order", "name")

    def get_name(self, obj):
        translation = self._get_translation(obj.translations.all())
        return translation.name if translation else None


class CategoryTreeSerializer(CategorySerializer):
    children = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ("children",)

    def get_children(self, obj):
        qs = obj.get_children().prefetch_related("translations")
        serializer = CategoryTreeSerializer(
            qs, many=True, context=self.context
        )
        return serializer.data


class BrandSerializer(TranslationMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ("id", "slug", "name")

    def get_name(self, obj):
        translation = self._get_translation(obj.translations.all())
        return translation.name if translation else None


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt", "is_main", "order", "variant_id")


class AttributeValueSerializer(TranslationMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = AttributeValue
        fields = ("id", "typed_value", "name", "attribute_id")

    def get_typed_value(self, obj):
        return obj.typed_value

    def get_name(self, obj):
        translations = obj.translations.all()
        translation = self._get_translation(translations)
        return translation.name if translation else None


class VariantAttributeSerializer(serializers.Serializer):
    attribute_slug = serializers.CharField()
    attribute_id = serializers.IntegerField()
    value_id = serializers.IntegerField()
    value = serializers.CharField(allow_null=True)
    value_name = serializers.CharField(allow_null=True)


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "price",
            "old_price",
            "stock",
            "is_active",
            "is_default",
            "attributes",
            "images",
        )

    def get_attributes(self, obj):
        language = self.context.get("language", "ru")

        single_qs = (
            ProductVariantAttribute.objects.filter(variant=obj)
            .select_related("attribute", "value")
            .prefetch_related(
                "value__translations",
            )
        )
        multi_qs = (
            ProductVariantMultiAttribute.objects.filter(variant=obj)
            .select_related("attribute", "value")
            .prefetch_related(
                "value__translations",
            )
        )

        items = []
        for rel in list(single_qs) + list(multi_qs):
            value = rel.value
            translations = list(value.translations.all())
            by_lang = {t.language: t for t in translations}
            t = by_lang.get(language) or by_lang.get("ru")

            items.append(
                {
                    "attribute_slug": rel.attribute.slug,
                    "attribute_id": rel.attribute_id,
                    "value_id": value.id,
                    "value": value.typed_value,
                    "value_name": t.name if t else None,
                }
            )

        return items


class ProductBaseSerializer(TranslationMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "slug",
            "category",
            "brand",
            "is_active",
            "min_price",
            "name",
            "description",
            "main_image",
        )

    def _get_translation_qs(self, obj):
        return obj.translations.all()

    def get_name(self, obj):
        translation = self._get_translation(self._get_translation_qs(obj))
        return translation.name if translation else None

    def get_description(self, obj):
        translation = self._get_translation(self._get_translation_qs(obj))
        return translation.description if translation else None

    def get_main_image(self, obj):
        image = obj.images.filter(is_main=True).first() or obj.images.first()
        if not image:
            return None
        return ProductImageSerializer(image, context=self.context).data


class ProductListSerializer(ProductBaseSerializer):
    class Meta(ProductBaseSerializer.Meta):
        fields = ProductBaseSerializer.Meta.fields


class ProductDetailSerializer(ProductBaseSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta(ProductBaseSerializer.Meta):
        fields = ProductBaseSerializer.Meta.fields + (
            "variants",
            "images",
            "created_at",
            "updated_at",
        )


class ProductFacetValueSerializer(serializers.Serializer):
    value = serializers.CharField()
    count = serializers.IntegerField()


class BrandFacetSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()


class PriceRangeFacetSerializer(serializers.Serializer):
    min = serializers.DecimalField(max_digits=12, decimal_places=2)
    max = serializers.DecimalField(max_digits=12, decimal_places=2)


class AttributeFacetValueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    value = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()


class AttributeFacetSerializer(serializers.Serializer):
    attribute_slug = serializers.CharField()
    values = AttributeFacetValueSerializer(many=True)

