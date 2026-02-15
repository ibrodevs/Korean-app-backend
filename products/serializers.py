from rest_framework import serializers
from .models import (
    WomenClothes, MenClothes, KidsClothes, Shoes,
    Accessories, Beauty, HomeProduct, Electronics, SportsProduct,
    Review, Order, OrderItem
)


class MultilingualSerializerMixin:
    """
    Mixin для поддержки мультиязычности в сериализаторах.
    
    Использование:
    class MySerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
        class Meta:
            multilingual_fields = ['name', 'description']  # поля с суффиксами _ru, _en, _kg
            ...
    """
    
    def get_multilingual_field(self, obj, field_name):
        """Получить значение поля на нужном языке"""
        language = self.context.get('language', 'ru')
        method_name = f'get_{field_name}'
        
        if hasattr(obj, method_name):
            return getattr(obj, method_name)(language)
            # flow: 1. getattr(obj, method_name) -> returns needed method. 2) (language) -> calls this method with argument called name. 3) return -> returns the result of method_name(language)
        
        # Fallback: прямое получение поля с суффиксом
        return getattr(obj, f'{field_name}_{language}', # -> this get's field without method. 
                    getattr(obj, f'{field_name}_ru', None)) # -> this is like fallback if it could find field with lang it will return field_name with _ru suffix   

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем поля для мультиязычных атрибутов
        multilingual_fields = getattr(self.Meta, 'multilingual_fields', [])
        
        for field_name in multilingual_fields:
            self.fields[field_name] = serializers.SerializerMethodField()
    
    def get_name(self, obj):
        """Получить name на нужном языке"""
        return self.get_multilingual_field(obj, 'name')
    
    def get_description(self, obj):
        """Получить description на нужном языке"""
        return self.get_multilingual_field(obj, 'description')


    
class WomenClothesSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = WomenClothes
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'size', 'color', 'material', 'season', 'brand',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class MenClothesSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MenClothes
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'size', 'color', 'material', 'style', 'brand',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class KidsClothesSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = KidsClothes
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'age_group', 'gender', 'color', 'material',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class ShoesSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Shoes
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'size', 'color', 'material', 'season', 'brand',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class AccessoriesSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Accessories
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'item_type', 'material', 'brand', 'color',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class BeautySerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Beauty
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'product_type', 'purpose', 'ingredients', 'volume', 'shelf_life',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class HomeProductSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = HomeProduct
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'item_type', 'material', 'dimensions', 'color',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class ElectronicsSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Electronics
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'brand', 'model', 'ram', 'storage', 'processor',
                  'condition', 'warranty_months',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class SportsProductSerializer(MultilingualSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SportsProduct
        multilingual_fields = ['name', 'description']
        fields = ('id', 'name', 'description', 'price', 'discount',
                  'sport_type', 'size', 'material', 'level',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name_ru', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'product', 'product_name', 'opinion', 'grade')


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product_content_type', 'product_object_id',
                  'quantity', 'price_at_purchase')


class OrderSerializer(serializers.ModelSerializer):
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'customer', 'customer_username', 'status', 'items',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказов"""
    class Meta:
        model = Order
        fields = ('id', 'customer', 'status', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
