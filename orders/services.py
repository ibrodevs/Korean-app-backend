"""
orders/services.py — business logic for the Orders module.

All public functions are meant to be called from views / tasks / webhooks.
Keep views lean: they validate input, call a service, return the response.
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from core.models import Cart, CartItem
from products.models import ProductVariant

from .models import Order, OrderItem, OrderStatusHistory

if TYPE_CHECKING:
    from core.models import CustomUser


# ─────────────────────────────────────────────────────────────────────────────
# create_order_from_cart
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def create_order_from_cart(*, user: "CustomUser", data: dict) -> Order:
    """
    Create an Order from the user's current Cart.

    Steps (all inside a single DB transaction):
      1. Fetch cart + items with select_for_update on variants (prevents overselling).
      2. Validate: cart not empty, variants active, stock sufficient.
      3. Create Order.
      4. Bulk-create OrderItems (snapshots).
      5. Recalculate totals.
      6. Deduct stock.
      7. Clear cart items.

    Args:
        user: The authenticated user placing the order.
        data: Validated data from CheckoutSerializer.

    Returns:
        The created Order instance.

    Raises:
        ValidationError: If the cart is empty, a variant is unavailable,
                         or stock is insufficient.
    """
    # ── 1. Fetch cart ─────────────────────────────────────────────────────────
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        raise ValidationError({"detail": "Cart not found. Add items before checkout."})

    cart_items = (
        CartItem.objects
        .filter(cart=cart)
        .select_related("variant__product")
    )

    if not cart_items.exists():
        raise ValidationError({"detail": "Your cart is empty."})

    # ── 2. Lock variants and validate stock ───────────────────────────────────
    variant_ids = [ci.variant_id for ci in cart_items]
    locked_variants: dict[int, ProductVariant] = {
        v.id: v
        for v in ProductVariant.objects
        .select_for_update()
        .select_related("product")
        .filter(id__in=variant_ids)
    }

    errors: list[str] = []
    for cart_item in cart_items:
        variant = locked_variants.get(cart_item.variant_id)

        if variant is None or not variant.is_active or not variant.product.is_active:
            errors.append(
                f"'{cart_item.variant.sku}' is no longer available."
            )
            continue

        if variant.stock < cart_item.quantity:
            errors.append(
                f"'{variant.sku}': only {variant.stock} in stock "
                f"(requested {cart_item.quantity})."
            )

    if errors:
        raise ValidationError({"detail": errors})

    # ── 3. Create Order ───────────────────────────────────────────────────────
    order = Order.objects.create(
        user=user,
        customer_email=user.email,
        customer_phone=data["customer_phone"],
        first_name=data["first_name"],
        last_name=data.get("last_name", ""),
        city=data.get("city", ""),
        address_line1=data.get("address_line1", ""),
        address_line2=data.get("address_line2", ""),
        postal_code=data.get("postal_code", ""),
        delivery_method=data["delivery_method"],
        payment_method=data["payment_method"],
        delivery_comment=data.get("delivery_comment", ""),
        pickup_location=data.get("pickup_location_id"),  # PickupLocation instance or None
    )

    # ── 4. Bulk-create OrderItems ─────────────────────────────────────────────
    items_to_create: list[OrderItem] = []
    for cart_item in cart_items:
        variant = locked_variants[cart_item.variant_id]

        # Resolve product name: prefer the 'ru' translation, then any, then slug
        translation = (
            variant.product.translations.filter(language="ru").first()
            or variant.product.translations.first()
        )
        product_name = translation.name if translation else variant.product.slug

        items_to_create.append(OrderItem(
            order=order,
            variant=variant,
            product_name=product_name,
            sku=variant.sku,
            unit_price=variant.price,
            quantity=cart_item.quantity,
            line_total=variant.price * cart_item.quantity,
        ))

    OrderItem.objects.bulk_create(items_to_create)

    # ── 5. Recalculate totals (save=False because we save below) ─────────────
    order.recalculate_totals(save=False)
    order.save(update_fields=["subtotal", "total_amount", "updated_at"])

    # ── 6. Deduct stock (single bulk UPDATE instead of N individual saves) ────
    variants_to_update = []
    for cart_item in cart_items:
        variant = locked_variants[cart_item.variant_id]
        variant.stock -= cart_item.quantity
        variants_to_update.append(variant)

    ProductVariant.objects.bulk_update(variants_to_update, ["stock"])

    # ── 7. Clear cart ─────────────────────────────────────────────────────────
    cart_items.delete()

    return order


# ─────────────────────────────────────────────────────────────────────────────
# cancel_order
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def cancel_order(
    *,
    order: Order,
    reason: str = "",
    changed_by: "CustomUser | None" = None,
) -> Order:
    """
    Cancel an order that is still in a cancelable state.

    - Only PENDING / CONFIRMED orders can be canceled by the customer.
    - Stock is restored for each OrderItem.
    - An OrderStatusHistory record is created.

    Raises:
        ValidationError: If the order cannot be canceled.
    """
    if not order.can_cancel:
        raise ValidationError({
            "detail": (
                f"Order #{order.order_number} cannot be canceled "
                f"(current status: {order.status})."
            )
        })

    old_status = order.status
    order.status = Order.Status.CANCELED
    from django.utils import timezone
    order.canceled_at = timezone.now()
    order.save(update_fields=["status", "canceled_at", "updated_at"])

    # Restore stock for each item in a single efficient query
    item_quantities = {}
    for item in order.items.filter(variant__isnull=False):
        item_quantities[item.variant_id] = item_quantities.get(item.variant_id, 0) + item.quantity

    if item_quantities:
        from django.db.models import Case, When, PositiveIntegerField
        ProductVariant.objects.filter(id__in=item_quantities.keys()).update(
            stock=Case(
                *[When(id=vid, then=F("stock") + qty) for vid, qty in item_quantities.items()],
                default=F("stock"),
                output_field=PositiveIntegerField()
            )
        )

    OrderStatusHistory.log_status_change(
        order=order,
        old_status=old_status,
        new_status=Order.Status.CANCELED,
        comment=reason,
        changed_by=changed_by,
    )

    return order


# ─────────────────────────────────────────────────────────────────────────────
# update_order_status  (internal / admin / webhook use)
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def update_order_status(
    *,
    order: Order,
    new_status: str,
    comment: str = "",
    changed_by: "CustomUser | None" = None,
) -> Order:
    """
    Change the order's status and record history.

    The status timestamp (*_at) is updated automatically via Order.save().
    """
    old_status = order.status
    if old_status == new_status:
        return order

    order.status = new_status
    order.save()  # triggers _update_status_timestamps via save()

    OrderStatusHistory.log_status_change(
        order=order,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
        changed_by=changed_by,
    )

    return order


# ─────────────────────────────────────────────────────────────────────────────
# update_payment_status  (for webhooks / payment provider callbacks)
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def update_payment_status(
    *,
    order: Order,
    new_payment_status: str,
    comment: str = "",
    changed_by: "CustomUser | None" = None,
) -> Order:
    """
    Update the payment status of an order and optionally auto-confirm it.

    When payment becomes PAID and the order is still PENDING, it is
    automatically moved to CONFIRMED.
    """
    old_payment_status = order.payment_status
    if old_payment_status == new_payment_status:
        return order

    order.payment_status = new_payment_status
    order.save()  # triggers paid_at via _update_status_timestamps

    # Auto-confirm pending orders that just got paid
    if (
        new_payment_status == Order.PaymentStatus.PAID
        and order.status == Order.Status.PENDING
    ):
        order = update_order_status(
            order=order,
            new_status=Order.Status.CONFIRMED,
            comment="Auto-confirmed after payment.",
            changed_by=changed_by,
        )

    OrderStatusHistory.log_status_change(
        order=order,
        old_status=f"payment:{old_payment_status}",
        new_status=f"payment:{new_payment_status}",
        comment=comment,
        changed_by=changed_by,
    )

    return order



