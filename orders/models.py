from decimal import Decimal
import secrets
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from products.models import ProductVariant


# ─────────────────────────────────────────────────────────────────────────────
# PickupLocation
# ─────────────────────────────────────────────────────────────────────────────

class PickupLocation(models.Model):
    """
    A physical self-pickup point that customers can choose at checkout.

    The Order model stores a live FK to this model and also snapshots
    the name, city, and address so historical orders remain correct even if
    the pickup point is later renamed, moved, or deleted.
    """

    city = models.CharField(max_length=120, verbose_name="City")
    name = models.CharField(max_length=255, verbose_name="Pickup point name")
    address = models.CharField(max_length=255, verbose_name="Address")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address line 2")

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        verbose_name="Latitude",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        verbose_name="Longitude",
    )

    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone")
    working_hours = models.CharField(max_length=255, blank=True, verbose_name="Working hours")

    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Is active")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Sort order")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pickup location"
        verbose_name_plural = "Pickup locations"
        ordering = ["sort_order", "city", "name"]
        indexes = [
            models.Index(fields=["city", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.city} — {self.name}"

class ArrivalWindow(models.Model):
    pickup_location = models.ForeignKey(PickupLocation, related_name='arrival_windows', on_delete=models.CASCADE)
    date = models.DateField()
    time_from = models.TimeField()
    time_to = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.pickup_location} {self.date} {self.time_from}-{self.time_to}"
# ─────────────────────────────────────────────────────────────────────────────
# Manager
# ─────────────────────────────────────────────────────────────────────────────

class OrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("user")

    def pending(self):
        return self.filter(status=Order.Status.PENDING)

    def unpaid(self):
        return self.filter(payment_status=Order.PaymentStatus.UNPAID)

    def today(self):
        return self.filter(created_at__date=timezone.now().date())


# ─────────────────────────────────────────────────────────────────────────────
# Order
# ─────────────────────────────────────────────────────────────────────────────

class Order(models.Model):
    # ── Constants ─────────────────────────────────────────────────────────────
    MIN_TOTAL_AMOUNT = Decimal("0.00")

    # ── Choices ───────────────────────────────────────────────────────────────
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELED = "canceled", "Canceled"
        REFUNDED = "refunded", "Refunded"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        MBANK = "mbank", "MBank"
        ELQR = "elqr", "ELQR"

    class DeliveryMethod(models.TextChoices):
        COURIER = "courier", "Courier"
        PICKUP = "pickup", "Pickup"

    # ── Primary keys ──────────────────────────────────────────────────────────
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # ── Relations ─────────────────────────────────────────────────────────────
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Customer account",
    )

    # ── Identifiers ───────────────────────────────────────────────────────────
    order_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name="Order number",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Order status",
    )
    payment_status = models.CharField(
        max_length=24,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
        verbose_name="Payment status",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        verbose_name="Payment method",
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.COURIER,
        verbose_name="Delivery method",
    )

    # ── Pickup location ───────────────────────────────────────────────────────
    pickup_location = models.ForeignKey(
        "PickupLocation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Pickup location",
    )
    # Snapshot fields — immutable once order is created
    pickup_location_name = models.CharField(
        max_length=255, blank=True, verbose_name="Pickup location name (snapshot)"
    )
    pickup_city = models.CharField(
        max_length=120, blank=True, verbose_name="Pickup city (snapshot)"
    )
    pickup_address = models.CharField(
        max_length=255, blank=True, verbose_name="Pickup address (snapshot)"
    )

    # ── Customer snapshot ─────────────────────────────────────────────────────
    customer_email = models.EmailField(verbose_name="Customer email")
    customer_phone = models.CharField(max_length=50, verbose_name="Customer phone")
    first_name = models.CharField(max_length=150, verbose_name="First name")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Last name")

    # ── Shipping snapshot ─────────────────────────────────────────────────────
    country = models.CharField(max_length=120, default="Kyrgyzstan", verbose_name="Country")
    # blank=True because for pickup orders these are auto-filled from PickupLocation in save();
    # courier delivery enforces non-blank via clean().
    city = models.CharField(max_length=120, blank=True, verbose_name="City")
    address_line1 = models.CharField(max_length=255, blank=True, verbose_name="Address line 1")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address line 2")
    postal_code = models.CharField(max_length=30, blank=True, verbose_name="Postal code")
    delivery_comment = models.TextField(blank=True, verbose_name="Delivery comment")

    # ── Money ─────────────────────────────────────────────────────────────────
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Subtotal",
    )
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Shipping cost",
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Discount amount",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Total amount",
    )

    # ── Misc ──────────────────────────────────────────────────────────────────
    notes = models.TextField(blank=True, verbose_name="Internal notes")

    # ── Status timestamps ─────────────────────────────────────────────────────
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Paid at")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Confirmed at")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="Shipped at")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Delivered at")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="Canceled at")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    # ── Manager ───────────────────────────────────────────────────────────────
    objects = OrderManager()

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["payment_status", "-created_at"]),
            models.Index(fields=["-created_at", "status"]),
            models.Index(fields=["paid_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_total_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name="order_subtotal_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"Order #{self.order_number}"

    # ── Validation ────────────────────────────────────────────────────────────

    def clean(self) -> None:
        """
        Custom model-level validation.
        Called automatically by forms and Django admin.
        In DRF, call order.full_clean() explicitly in the serializer/service.
        """
        if self.discount_amount and self.subtotal is not None:
            max_discount = self.subtotal + (self.shipping_cost or Decimal("0.00"))
            if self.discount_amount > max_discount:
                raise ValidationError({
                    "discount_amount": "Discount cannot exceed (subtotal + shipping_cost)."
                })

        if self.payment_status == self.PaymentStatus.PAID and not self.paid_at:
            raise ValidationError({
                "payment_status": "A paid order must have a paid_at timestamp."
            })

        # Pickup / courier cross-validation
        is_pickup = self.delivery_method == self.DeliveryMethod.PICKUP
        has_location = bool(self.pickup_location_id)

        if is_pickup and not has_location:
            raise ValidationError({
                "pickup_location": "A pickup location is required when delivery method is 'pickup'."
            })

        if not is_pickup and has_location:
            raise ValidationError({
                "pickup_location": "Pickup location must be empty for courier delivery."
            })

        # For courier, city and address_line1 are mandatory.
        # For pickup, they are auto-filled from the PickupLocation in save(),
        # so we skip this check (they may legitimately be blank at clean() time).
        if not is_pickup:
            address_errors: dict[str, str] = {}
            if not self.city:
                address_errors["city"] = "City is required for courier delivery."
            if not self.address_line1:
                address_errors["address_line1"] = "Address line 1 is required for courier delivery."
            if address_errors:
                raise ValidationError(address_errors)

    # ── Persistence ───────────────────────────────────────────────────────────

    @staticmethod
    def generate_order_number() -> str:
        """
        Generate a unique human-readable order number.
        Uses cryptographically-safe randomness (secrets) instead of random.randint.
        Example: ORD-20260312-847291
        """
        date_str = timezone.now().strftime("%Y%m%d")
        random_part = secrets.randbelow(900_000) + 100_000  # 100000–999999
        return f"ORD-{date_str}-{random_part}"

    def _update_status_timestamps(self, old_status: str, old_payment_status: str) -> None:
        """
        Auto-fill the *_at timestamp fields when status or payment_status changes.
        Note: paid_at is triggered by PaymentStatus.PAID, all others by Status.
        """
        now = timezone.now()

        # Order status → timestamp field
        status_map: dict[str, str] = {
            self.Status.CONFIRMED: "confirmed_at",
            self.Status.SHIPPED: "shipped_at",
            self.Status.DELIVERED: "delivered_at",
            self.Status.CANCELED: "canceled_at",
        }
        if self.status != old_status:
            if field := status_map.get(self.status):
                setattr(self, field, now)

        # Payment status → paid_at
        if (
            self.payment_status != old_payment_status
            and self.payment_status == self.PaymentStatus.PAID
            and not self.paid_at
        ):
            self.paid_at = now

    def save(self, *args, **kwargs) -> None:
        # ── Auto-snapshot pickup location address ─────────────────────────────
        # Only on first save (new order) so the snapshot stays immutable.
        if not self.pk and self.delivery_method == self.DeliveryMethod.PICKUP:
            loc = self.pickup_location
            if loc:
                self.pickup_location_name = self.pickup_location_name or loc.name
                self.pickup_city = self.pickup_city or loc.city
                self.pickup_address = self.pickup_address or loc.address
                # Also fill standard shipping snapshot fields if blank
                if not self.city:
                    self.city = loc.city
                if not self.address_line1:
                    self.address_line1 = loc.address

        if not self.order_number:
            # Crypto-safe generation with collision retry
            candidate = self.generate_order_number()
            while Order.objects.filter(order_number=candidate).exists():
                candidate = self.generate_order_number()
            self.order_number = candidate

        # Auto-update status timestamps on changes to existing orders
        if self.pk:
            try:
                old = Order.objects.get(pk=self.pk)
                self._update_status_timestamps(old.status, old.payment_status)
            except Order.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    # ── Business logic ────────────────────────────────────────────────────────

    def recalculate_totals(self, save: bool = True) -> None:
        """
        Recalculate subtotal and total_amount from related OrderItems.

        Args:
            save: If True (default), persists the updated fields immediately.
                  Pass False when you intend to call save() yourself afterward.
        """
        try:
            subtotal = sum(item.line_total for item in self.items.all())
            self.subtotal = subtotal
            total = subtotal + self.shipping_cost - self.discount_amount
            self.total_amount = max(total, self.MIN_TOTAL_AMOUNT)

            if save:
                self.save(update_fields=["subtotal", "total_amount", "updated_at"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Error recalculating totals for order {self.order_number}: {exc}"
            ) from exc

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        """Customer's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_address(self) -> str:
        """Formatted shipping address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.country}")
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    @property
    def is_paid(self) -> bool:
        return self.payment_status == self.PaymentStatus.PAID

    @property
    def can_cancel(self) -> bool:
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)

    @property
    def total_items(self) -> int:
        return self.items.aggregate(models.Sum("quantity"))["quantity__sum"] or 0


# ─────────────────────────────────────────────────────────────────────────────
# OrderItem
# ─────────────────────────────────────────────────────────────────────────────

class OrderItem(models.Model):
    # ── Relations ─────────────────────────────────────────────────────────────
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Order",
    )
    # SET_NULL: variant can be deleted without destroying the order snapshot
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Product variant",
    )

    # ── Snapshot ──────────────────────────────────────────────────────────────
    product_name = models.CharField(max_length=255, verbose_name="Product name")
    sku = models.CharField(max_length=100, db_index=True, verbose_name="SKU")
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Unit price",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantity",
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Line total",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["sku"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="order_item_unit_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order.order_number} – {self.sku} x{self.quantity}"

    def save(self, *args, **kwargs) -> None:
        # Track whether price/quantity changed on an existing item
        recalculate = False
        if self.pk:
            try:
                old = OrderItem.objects.get(pk=self.pk)
                recalculate = (
                    old.quantity != self.quantity or old.unit_price != self.unit_price
                )
            except OrderItem.DoesNotExist:
                pass

        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

        # Propagate changes to the parent order's totals.
        # Skipped during bulk_create (pk is None before save in that flow),
        # so call order.recalculate_totals() explicitly after bulk_create.
        if recalculate:
            self.order.recalculate_totals(save=True)


# ─────────────────────────────────────────────────────────────────────────────
# OrderStatusHistory
# ─────────────────────────────────────────────────────────────────────────────

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Order",
    )
    old_status = models.CharField(max_length=20, blank=True, verbose_name="Previous status")
    new_status = models.CharField(max_length=20, verbose_name="New status")
    comment = models.TextField(blank=True, verbose_name="Comment")

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changed_order_statuses",
        verbose_name="Changed by",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Changed at")

    class Meta:
        verbose_name = "Order status history"
        verbose_name_plural = "Order status history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
            models.Index(fields=["new_status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.order.order_number}: {self.old_status or '–'} → {self.new_status}"

    @classmethod
    def log_status_change(
        cls,
        order: "Order",
        new_status: str,
        *,
        old_status: str | None = None,
        comment: str = "",
        changed_by=None,
    ) -> "OrderStatusHistory":
        """
        Convenience factory — create a history entry in one call.

        Usage:
            OrderStatusHistory.log_status_change(
                order, Order.Status.SHIPPED, changed_by=request.user
            )
        """
        if old_status is None:
            old_status = order.status if order.pk else ""

        return cls.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            changed_by=changed_by,
        )

class Coupon(models.Model):
    PERCENT = 'percent'
    FIXED = 'fixed'
    DISCOUNT_TYPES = [
        (PERCENT, 'percent'),
        (FIXED, 'fixed')
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    value = models.IntegerField()
    min_order_amount = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code