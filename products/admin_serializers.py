from django.db import transaction
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
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
    AttributeTextValue,
    AttributeIntValue,
    AttributeFloatValue,
    AttributeBooleanValue,
    AttributeColorValue,
    ProductVariantAttribute,
    ProductVariantMultiAttribute,
)


class CategoryTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryTranslation
        fields = ("id", "language", "name")


class AdminCategorySerializer(serializers.ModelSerializer):
    translations = CategoryTranslationSerializer(many=True, required=False)

    class Meta:
        model = Category
        fields = ("id", "slug", "parent", "order", "translations")

    def validate_translations(self, value):
        languages = [t.get("language") for t in value if "language" in t]
        if len(languages) != len(set(languages)):
            raise serializers.ValidationError("Language already exists in translations payload.")
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        category = Category.objects.create(**validated_data)
        for t_data in translations_data:
            CategoryTranslation.objects.create(category=category, **t_data)
        return category

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if translations_data is not None:
            # Simple approach: clear and recreate or update by language
            existing_translations = {t.language: t for t in instance.translations.all()}
            for t_data in translations_data:
                lang = t_data["language"]
                if lang in existing_translations:
                    t_inst = existing_translations[lang]
                    t_inst.name = t_data.get("name", t_inst.name)
                    t_inst.save()
                else:
                    CategoryTranslation.objects.create(category=instance, **t_data)
        return instance


class BrandTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandTranslation
        fields = ("id", "language", "name")


class AdminBrandSerializer(serializers.ModelSerializer):
    translations = BrandTranslationSerializer(many=True, required=False)

    class Meta:
        model = Brand
        fields = ("id", "slug", "translations")

    def validate_translations(self, value):
        languages = [t.get("language") for t in value if "language" in t]
        if len(languages) != len(set(languages)):
            raise serializers.ValidationError("Language already exists in translations payload.")
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        brand = Brand.objects.create(**validated_data)
        for t_data in translations_data:
            BrandTranslation.objects.create(brand=brand, **t_data)
        return brand

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if translations_data is not None:
            existing_translations = {t.language: t for t in instance.translations.all()}
            for t_data in translations_data:
                lang = t_data["language"]
                if lang in existing_translations:
                    t_inst = existing_translations[lang]
                    t_inst.name = t_data.get("name", t_inst.name)
                    t_inst.save()
                else:
                    BrandTranslation.objects.create(brand=instance, **t_data)
        return instance


class AttributeTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeTranslation
        fields = ("id", "language", "name")


class AdminAttributeSerializer(serializers.ModelSerializer):
    translations = AttributeTranslationSerializer(many=True, required=False)

    class Meta:
        model = Attribute
        fields = ("id", "slug", "value_type", "is_multiple", "translations")

    def validate_translations(self, value):
        languages = [t.get("language") for t in value if "language" in t]
        if len(languages) != len(set(languages)):
            raise serializers.ValidationError("Language already exists in translations payload.")
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        attribute = Attribute.objects.create(**validated_data)
        for t_data in translations_data:
            AttributeTranslation.objects.create(attribute=attribute, **t_data)
        return attribute
        
    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        # Value type immutable
        validated_data.pop("value_type", None) 
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if translations_data is not None:
            existing_translations = {t.language: t for t in instance.translations.all()}
            for t_data in translations_data:
                lang = t_data["language"]
                if lang in existing_translations:
                    t_inst = existing_translations[lang]
                    t_inst.name = t_data.get("name", t_inst.name)
                    t_inst.save()
                else:
                    AttributeTranslation.objects.create(attribute=instance, **t_data)
        return instance


class AttributeValueTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValueTranslation
        fields = ("id", "language", "name")


class AdminAttributeValueSerializer(serializers.ModelSerializer):
    translations = AttributeValueTranslationSerializer(many=True, required=False)
    value = serializers.JSONField(write_only=True)
    typed_value = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AttributeValue
        fields = ("id", "attribute", "value", "typed_value", "translations")

    def validate_translations(self, value):
        languages = [t.get("language") for t in value if "language" in t]
        if len(languages) != len(set(languages)):
            raise serializers.ValidationError("Language already exists in translations payload.")
        return value

    def get_typed_value(self, obj):
        return obj.typed_value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        value_data = validated_data.pop("value")
        attribute = validated_data["attribute"]
        
        with transaction.atomic():
            attr_value = AttributeValue.objects.create(**validated_data)
            
            # Create typed value
            val_type = attribute.value_type
            import re
            try:
                if val_type == "text":
                    AttributeTextValue.objects.create(base=attr_value, value=value_data)
                elif val_type == "int":
                    AttributeIntValue.objects.create(base=attr_value, value=int(value_data))
                elif val_type == "float":
                    AttributeFloatValue.objects.create(base=attr_value, value=float(value_data))
                elif val_type == "boolean":
                    val_str = str(value_data).lower()
                    if val_str not in ("true", "false", "1", "0"):
                        raise ValueError("Invalid boolean")
                    AttributeBooleanValue.objects.create(base=attr_value, value=val_str in ("true", "1"))
                elif val_type == "color":
                    if not re.match(r"^#[0-9a-fA-F]{6}$", str(value_data)):
                        raise ValueError("Invalid color")
                    AttributeColorValue.objects.create(base=attr_value, value=value_data)
            except ValueError as e:
                raise serializers.ValidationError({"value": f"{str(e)}: Invalid value for type {val_type}"})

            for t_data in translations_data:
                AttributeValueTranslation.objects.create(value=attr_value, **t_data)
                
        return attr_value

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        value_data = validated_data.pop("value", None)
        
        # We generally do not change attribute
        validated_data.pop("attribute", None)
        
        with transaction.atomic():
            if value_data is not None:
                val_type = instance.attribute.value_type
                import re
                try:
                    if val_type == "text":
                        inst = instance.text
                        inst.value = value_data
                        inst.save()
                    elif val_type == "int":
                        inst = instance.int
                        inst.value = int(value_data)
                        inst.save()
                    elif val_type == "float":
                        inst = instance.float
                        inst.value = float(value_data)
                        inst.save()
                    elif val_type == "boolean":
                        val_str = str(value_data).lower()
                        if val_str not in ("true", "false", "1", "0"):
                            raise ValueError("Invalid boolean")
                        inst = instance.boolean
                        inst.value = val_str in ("true", "1")
                        inst.save()
                    elif val_type == "color":
                        if not re.match(r"^#[0-9a-fA-F]{6}$", str(value_data)):
                            raise ValueError("Invalid color")
                        inst = instance.color
                        inst.value = value_data
                        inst.save()
                except ValueError as e:
                    raise serializers.ValidationError({"value": f"{str(e)}: Invalid value for type {val_type}"})

            if translations_data is not None:
                existing_translations = {t.language: t for t in instance.translations.all()}
                for t_data in translations_data:
                    lang = t_data["language"]
                    if lang in existing_translations:
                        t_inst = existing_translations[lang]
                        t_inst.name = t_data.get("name", t_inst.name)
                        t_inst.save()
                    else:
                        AttributeValueTranslation.objects.create(value=instance, **t_data)

        return instance


class AdminProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "product", "variant", "image", "alt", "is_main", "order")
        read_only_fields = ("product", "variant")

    def create(self, validated_data):
        with transaction.atomic():
            is_main = validated_data.get("is_main", False)
            if is_main:
                product = validated_data.get("product")
                ProductImage.objects.filter(product=product).update(is_main=False)
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            is_main = validated_data.get("is_main", instance.is_main)
            if is_main and not instance.is_main:
                product = validated_data.get("product", instance.product)
                ProductImage.objects.filter(product=product).update(is_main=False)
            return super().update(instance, validated_data)


from decimal import Decimal

class AdminProductVariantBulkPriceSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, min_value=Decimal('0.00'))

class AdminProductVariantBulkStockSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    stock = serializers.IntegerField(required=True, min_value=0)


class VariantAttributeWriteSerializer(serializers.Serializer):
    attribute = serializers.SlugField() # Using slug as requested
    value = serializers.CharField()


class AdminProductVariantSerializer(serializers.ModelSerializer):
    attributes = VariantAttributeWriteSerializer(many=True, required=False, write_only=True)
    images = AdminProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "sku",
            "price",
            "old_price",
            "stock",
            "is_active",
            "is_default",
            "attributes",
            "images"
        )
        read_only_fields = ("product",) # Typically set via context or URL

    def create(self, validated_data):
        attributes_data = validated_data.pop("attributes", [])
        
        with transaction.atomic():
            is_default = validated_data.get("is_default", False)
            product = validated_data.get("product")
            if is_default:
                ProductVariant.objects.filter(product=product).update(is_default=False)
            elif not ProductVariant.objects.filter(product=product).exists():
                validated_data["is_default"] = True

            variant = ProductVariant.objects.create(**validated_data)
            self._handle_attributes(variant, attributes_data)
            self._update_product_min_price(product)
            
        return variant

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop("attributes", None)
        
        with transaction.atomic():
            is_default = validated_data.get("is_default", instance.is_default)
            if is_default and not instance.is_default:
                ProductVariant.objects.filter(product=instance.product).update(is_default=False)
                
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if attributes_data is not None:
                ProductVariantAttribute.objects.filter(variant=instance).delete()
                ProductVariantMultiAttribute.objects.filter(variant=instance).delete()
                self._handle_attributes(instance, attributes_data)
                
            self._update_product_min_price(instance.product)
                
        return instance

    def _update_product_min_price(self, product):
        min_variant = product.variants.filter(is_active=True).order_by("price").first()
        if min_variant:
            product.min_price = min_variant.price
            product.save(update_fields=["min_price"])

    def _handle_attributes(self, variant, attributes_data):
        seen_single_attributes = set()
        for attr_item in attributes_data:
            attr_slug = attr_item["attribute"]
            value_raw = attr_item["value"]
            
            try:
                attribute = Attribute.objects.get(slug=attr_slug)
            except Attribute.DoesNotExist:
                raise serializers.ValidationError(f"Attribute {attr_slug} does not exist.")

            if not attribute.is_multiple:
                if attribute.id in seen_single_attributes:
                    raise serializers.ValidationError(f"Cannot assign multiple values to a single attribute: {attr_slug}")
                seen_single_attributes.add(attribute.id)

            # Find or create AttributeValue
            attr_val = self._get_or_create_attribute_value(attribute, value_raw)
            
            if attribute.is_multiple:
                ProductVariantMultiAttribute.objects.get_or_create(
                    variant=variant,
                    attribute=attribute,
                    value=attr_val
                )
            else:
                ProductVariantAttribute.objects.update_or_create(
                    variant=variant,
                    attribute=attribute,
                    defaults={"value": attr_val}
                )

    def _get_or_create_attribute_value(self, attribute, value_raw):
        # Determine value to query
        val_type = attribute.value_type
        
        # Simplified find/create for scalar values, without translations
        if val_type == "text":
            text_val, created = AttributeTextValue.objects.get_or_create(value=value_raw, defaults={"base": AttributeValue.objects.create(attribute=attribute)})
            return text_val.base
        elif val_type == "int":
            int_val, created = AttributeIntValue.objects.get_or_create(value=int(value_raw), defaults={"base": AttributeValue.objects.create(attribute=attribute)})
            return int_val.base
        elif val_type == "float":
            float_val, created = AttributeFloatValue.objects.get_or_create(value=float(value_raw), defaults={"base": AttributeValue.objects.create(attribute=attribute)})
            return float_val.base
        elif val_type == "boolean":
            bool_val, created = AttributeBooleanValue.objects.get_or_create(value=str(value_raw).lower() in ("true", "1"), defaults={"base": AttributeValue.objects.create(attribute=attribute)})
            return bool_val.base
        elif val_type == "color":
            color_val, created = AttributeColorValue.objects.get_or_create(value=value_raw, defaults={"base": AttributeValue.objects.create(attribute=attribute)})
            return color_val.base


class ProductTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTranslation
        fields = ("id", "language", "name", "description", "meta_title", "meta_description", "meta_keywords")


class AdminProductSerializer(serializers.ModelSerializer):
    translations = ProductTranslationSerializer(many=True, required=False)
    variants = AdminProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "slug",
            "category",
            "brand",
            "is_active",
            "min_price",
            "translations",
            "variants"
        )

    def validate_translations(self, value):
        languages = [t.get("language") for t in value if "language" in t]
        if len(languages) != len(set(languages)):
            raise serializers.ValidationError("Language already exists in translations payload.")
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        variants_data = validated_data.pop("variants", [])
        
        with transaction.atomic():
            product = Product.objects.create(**validated_data)
            
            for t_data in translations_data:
                ProductTranslation.objects.create(product=product, **t_data)
                
            for v_data in variants_data:
                attributes_data = v_data.pop("attributes", [])
                
                is_default = v_data.get("is_default", False)
                if is_default:
                    ProductVariant.objects.filter(product=product).update(is_default=False)
                elif not ProductVariant.objects.filter(product=product).exists():
                    v_data["is_default"] = True
                    
                variant = ProductVariant.objects.create(product=product, **v_data)
                
                # Cannot use self._handle_attributes since it's on Variant serializer
                variant_serializer = AdminProductVariantSerializer()
                variant_serializer._handle_attributes(variant, attributes_data)

            self._update_min_price(product)
            
        return product

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        validated_data.pop("variants", None)
        
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if translations_data is not None:
                existing_translations = {t.language: t for t in instance.translations.all()}
                for t_data in translations_data:
                    lang = t_data["language"]
                    if lang in existing_translations:
                        t_inst = existing_translations[lang]
                        t_inst.name = t_data.get("name", t_inst.name)
                        t_inst.description = t_data.get("description", t_inst.description)
                        t_inst.meta_title = t_data.get("meta_title", t_inst.meta_title)
                        t_inst.meta_description = t_data.get("meta_description", t_inst.meta_description)
                        t_inst.meta_keywords = t_data.get("meta_keywords", t_inst.meta_keywords)
                        t_inst.save()
                    else:
                        ProductTranslation.objects.create(product=instance, **t_data)
                        
            # We typically do not update variants deeply via Product update in DRF to keep it sane,
            # but if supplied, we could. The instructions say Admin panel can attach variants.
            # Usually it's better to POST to /admin/products/{id}/variants/.
            
        return instance

    def _update_min_price(self, product):
        min_variant = product.variants.filter(is_active=True).order_by("price").first()
        if min_variant:
            product.min_price = min_variant.price
            product.save(update_fields=["min_price"])
