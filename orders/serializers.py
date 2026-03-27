from rest_framework import serializers

from .models import Order, OrderItem, PickupLocation, Cart, CartItem


# ─────────────────────────────────────────────────────────────────────────────
# PickupLocation
# ─────────────────────────────────────────────────────────────────────────────

class PickupLocationSerializer(serializers.ModelSerializer):
    """Read-only serializer for active pickup locations (used in list endpoint)."""

    class Meta:
        model = PickupLocation
        fields = [
            "id",
            "city",
            "name",
            "address",
            "address_line2",
            "latitude",
            "longitude",
            "phone",
            "working_hours",
        ]


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
            # pickup
            "pickup_location",
            "pickup_location_name",
            "pickup_city",
            "pickup_address",
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

    city = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    postal_code = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    delivery_comment = serializers.CharField(required=False, allow_blank=True, default="")

    delivery_method = serializers.ChoiceField(choices=Order.DeliveryMethod.choices)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)

    # Optional for courier, required for pickup — validated in validate()
    pickup_location_id = serializers.PrimaryKeyRelatedField(
        queryset=PickupLocation.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        default=None,
    )

    def validate(self, data):
        delivery = data.get("delivery_method")
        pickup_loc = data.get("pickup_location_id")

        if delivery == Order.DeliveryMethod.PICKUP:
            if not pickup_loc:
                raise serializers.ValidationError({
                    "pickup_location_id": "This field is required when delivery_method is 'pickup'."
                })
            # Location must be active (queryset already filters, but be explicit)
            if not pickup_loc.is_active:
                raise serializers.ValidationError({
                    "pickup_location_id": "The selected pickup location is currently inactive."
                })

        if delivery == Order.DeliveryMethod.COURIER and pickup_loc:
            raise serializers.ValidationError({
                "pickup_location_id": "Pickup location must be empty for courier delivery."
            })

        # For courier delivery, city and address_line1 are required
        if delivery == Order.DeliveryMethod.COURIER:
            if not data.get("city"):
                raise serializers.ValidationError({"city": "This field is required for courier delivery."})
            if not data.get("address_line1"):
                raise serializers.ValidationError({"address_line1": "This field is required for courier delivery."})

        return data


class OrderCancelSerializer(serializers.Serializer):
    """Input for POST /orders/{id}/cancel/"""

    reason = serializers.CharField(required=False, allow_blank=True, default="")



class CartItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product_variant", "quantity", "line_total"]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    import_fee = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    has_out_of_stock = serializers.BooleanField(read_only=True)
    has_inactive_variant = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "subtotal", "import_fee", "discount", "total", "has_out_of_stock", "has_inactive_variant"]


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)

class CouponResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    discount = serializers.DecimalField(max_digits=12, decimal_places=2)


coupon_code = serializers.CharField(required=False, allow_blank=True, default="")


def validate(self, data):
    data = super().validate(data)

    code = data.get("coupon_code")
    if code:
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"coupon_code": "Invalid or inactive coupon."})

        min_amount = coupon.min_order_amount
        cart_subtotal = data.get("subtotal", 0)
        if min_amount and cart_subtotal < min_amount:
            raise serializers.ValidationError({"coupon_code": f"Coupon requires minimum order amount {min_amount}"})

    return data