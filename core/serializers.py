from rest_framework import serializers
from rest_framework.response import Response
from .models import CustomUser

class WriteUserSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'phone', 'photo', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'password': {'write_only' : True}
            }
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('password must be at least 8 characters')
        
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain a capital letter.")
        
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain a digit letter.")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class ListUserSerializer(serializers.ModelSerializer):
     class Meta:
        model = CustomUser
        fields = ('email', 'photo', 'first_name', 'last_name')

from products.models import ProductVariant
from .models import Cart, CartItem

class CartItemCreateSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_variant_id(self, value):
        try:
            variant = ProductVariant.objects.select_related("product").get(
                id=value,
                is_active=True,
                product__is_active=True,
            )
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Активный вариант товара не найден.")
        return value


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source="variant.id", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    price = serializers.DecimalField(
        source="variant.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    old_price = serializers.DecimalField(
        source="variant.old_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )
    stock = serializers.IntegerField(source="variant.stock", read_only=True)
    variant_is_active = serializers.BooleanField(source="variant.is_active", read_only=True)
    product_id = serializers.IntegerField(source="variant.product.id", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant_id",
            "sku",
            "price",
            "old_price",
            "stock",
            "variant_is_active",
            "product_id",
            "product_slug",
            "quantity",
            "total_price",
            "added_at",
        ]

    def get_total_price(self, obj):
        return obj.variant.price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "total_items",
            "total_quantity",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def get_total_items(self, obj):
        return obj.items.count()

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(item.variant.price * item.quantity for item in obj.items.all())