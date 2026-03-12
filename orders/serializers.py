from rest_framework import serializers

from .models import Order, OrderItem


# ─────────────────────────────────────────────────────────────────────────────
# Read-only sub-serializer
# ─────────────────────────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "sku",
            "unit_price",
            "quantity",
            "line_total",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Customer-facing read serializers
# ─────────────────────────────────────────────────────────────────────────────

class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the order list endpoint."""

    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "uuid",
            "order_number",
            "status",
            "payment_status",
            "payment_method",
            "delivery_method",
            "total_amount",
            "total_items",
            "created_at",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full serializer for order detail — includes items and computed fields."""

    items = OrderItemSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    full_address = serializers.CharField(read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "uuid",
            "order_number",
            "status",
            "payment_status",
            "payment_method",
            "delivery_method",
            # customer snapshot
            "customer_email",
            "customer_phone",
            "first_name",
            "last_name",
            "full_name",
            # shipping snapshot
            "country",
            "city",
            "address_line1",
            "address_line2",
            "postal_code",
            "full_address",
            "delivery_comment",
            # money
            "subtotal",
            "shipping_cost",
            "discount_amount",
            "total_amount",
            # misc
            "notes",
            "total_items",
            "items",
            # timestamps
            "paid_at",
            "confirmed_at",
            "shipped_at",
            "delivered_at",
            "canceled_at",
            "created_at",
            "updated_at",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Write serializers
# ─────────────────────────────────────────────────────────────────────────────

class CheckoutSerializer(serializers.Serializer):
    """Input for POST /orders/checkout/"""

    customer_phone = serializers.CharField(max_length=50)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    city = serializers.CharField(max_length=120)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    postal_code = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    delivery_comment = serializers.CharField(required=False, allow_blank=True, default="")

    delivery_method = serializers.ChoiceField(choices=Order.DeliveryMethod.choices)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)


class OrderCancelSerializer(serializers.Serializer):
    """Input for POST /orders/{id}/cancel/"""

    reason = serializers.CharField(required=False, allow_blank=True, default="")
