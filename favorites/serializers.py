from rest_framework import serializers
from .models import Favorite


class FavoriteProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    price = serializers.DecimalField(source="min_price", max_digits=12, decimal_places=2, allow_null=True)
    image = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    def get_name(self, obj):
        lang = self.context.get("lang", "ru")
        translations = list(obj.translations.all())
        by_lang = {t.language: t for t in translations}
        t = by_lang.get(lang) or by_lang.get("ru")
        return t.name if t else obj.slug

    def get_image(self, obj):
        image = obj.images.filter(is_main=True).first() or obj.images.first()
        if not image:
            return None
        request = self.context.get("request")
        if request and image.image:
            return request.build_absolute_uri(image.image.url)
        return image.image.url if image.image else None

    def get_stock_status(self, obj):
        variants = obj.variants.filter(is_active=True)
        total_stock = sum(v.stock for v in variants)
        if total_stock <= 0:
            return "out_of_stock"
        if total_stock < 5:
            return "low_stock"
        return "in_stock"


class FavoriteListSerializer(serializers.ModelSerializer):
    product = FavoriteProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "product")


class FavoriteCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
