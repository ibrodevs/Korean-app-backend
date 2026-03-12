"""
Orders API Tests
================
Coverage:

  Checkout (POST /api/v1/orders/checkout/)
    test_checkout_success_creates_order                          (1)
    test_checkout_creates_order_items_with_snapshot             (2)
    test_checkout_deducts_stock                                 (3)
    test_checkout_clears_cart                                   (4)
    test_checkout_empty_cart_returns_400                        (5)
    test_checkout_no_cart_returns_400                           (6)
    test_checkout_inactive_variant_returns_400                  (7)
    test_checkout_inactive_product_returns_400                  (8)
    test_checkout_insufficient_stock_returns_400                (9)
    test_checkout_missing_required_fields_returns_400          (10)
    test_checkout_invalid_delivery_method_returns_400          (11)
    test_checkout_invalid_payment_method_returns_400           (12)
    test_checkout_requires_auth                                (13)
    test_checkout_order_number_format                          (14)
    test_checkout_response_contains_items                      (15)

  My Order List (GET /api/v1/orders/)
    test_list_returns_only_own_orders                          (16)
    test_list_returns_200_when_no_orders                       (17)
    test_list_requires_auth                                    (18)
    test_list_filter_by_status                                 (19)
    test_list_filter_by_payment_status                         (20)
    test_list_order_number_in_response                         (21)

  My Order Detail (GET /api/v1/orders/{id}/)
    test_detail_returns_full_order                             (22)
    test_detail_contains_items                                 (23)
    test_detail_computed_properties                            (24)
    test_detail_requires_auth                                  (25)
    test_detail_own_order_returns_200                          (26)
    test_detail_other_user_order_returns_404                   (27)
    test_detail_nonexistent_returns_404                        (28)

  Cancel Order (POST /api/v1/orders/{id}/cancel/)
    test_cancel_pending_order_success                          (29)
    test_cancel_confirmed_order_success                        (30)
    test_cancel_restores_stock                                 (31)
    test_cancel_creates_status_history                         (32)
    test_cancel_shipped_order_returns_400                      (33)
    test_cancel_delivered_order_returns_400                    (34)
    test_cancel_other_user_order_returns_404                   (35)
    test_cancel_already_canceled_returns_400                   (36)
    test_cancel_requires_auth                                  (37)
    test_cancel_with_reason_stored_in_history                  (38)

  Services (unit)
    test_service_update_order_status_records_history           (39)
    test_service_update_payment_status_auto_confirms           (40)

Total: 40 + 24 edge-case + 11 pickup = 75 tests
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Cart, CartItem, CustomUser
from orders.models import Order, OrderItem, OrderStatusHistory, PickupLocation
from orders.services import update_order_status, update_payment_status
from products.models import Category, Product, ProductTranslation, ProductVariant

# ─────────────────────────────────────────────────────────────────────────────
# Shared factory helpers
# ─────────────────────────────────────────────────────────────────────────────

CHECKOUT_URL = "/api/v1/orders/checkout/"
LIST_URL = "/api/v1/orders/"
PICKUP_LOCATIONS_URL = "/api/v1/orders/pickup-locations/"


def order_detail_url(pk):
    return f"/api/v1/orders/{pk}/"


def order_cancel_url(pk):
    return f"/api/v1/orders/{pk}/cancel/"


def make_user(email="user@orders.test", password="Test1234!"):
    return CustomUser.objects.create_user(email=email, password=password)


def make_product(slug="korean-cream", is_active=True):
    category, _ = Category.objects.get_or_create(slug="skincare")
    product = Product.objects.create(
        category=category,
        slug=slug,
        is_active=is_active,
        min_price=Decimal("5000.00"),
    )
    ProductTranslation.objects.create(
        product=product,
        language="ru",
        name="Корейский крем",
        description="Описание",
    )
    return product


def make_variant(product, sku="SKU-001", price="5000.00", stock=20, is_active=True):
    return ProductVariant.objects.create(
        product=product,
        sku=sku,
        price=Decimal(price),
        stock=stock,
        is_active=is_active,
    )


VALID_CHECKOUT_PAYLOAD = {
    "customer_phone": "+996700000001",
    "first_name": "Адиль",
    "last_name": "Тестов",
    "city": "Bishkek",
    "address_line1": "Manas 10",
    "delivery_method": "courier",
    "payment_method": "mbank",
}


# ─────────────────────────────────────────────────────────────────────────────
# Base test class
# ─────────────────────────────────────────────────────────────────────────────

class OrdersBaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

        self.product = make_product()
        self.variant = make_variant(self.product, sku="V-001", stock=20)
        self.variant2 = make_variant(self.product, sku="V-002", stock=5, price="2000.00")

        # Cart with 1 item ready for checkout
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, variant=self.variant, quantity=2
        )

    # ── Shortcuts ─────────────────────────────────────────────────────────────
    def checkout(self, payload=None):
        return self.client.post(CHECKOUT_URL, payload or VALID_CHECKOUT_PAYLOAD, format="json")

    def get_list(self, params=""):
        return self.client.get(f"{LIST_URL}{params}")

    def get_detail(self, pk):
        return self.client.get(order_detail_url(pk))

    def cancel(self, pk, payload=None):
        return self.client.post(order_cancel_url(pk), payload or {}, format="json")

    def _make_order(self, user=None, status=Order.Status.PENDING):
        """Directly create an order in DB without going through checkout."""
        u = user or self.user
        order = Order.objects.create(
            user=u,
            customer_email=u.email,
            customer_phone="+996700000001",
            first_name="Test",
            city="Bishkek",
            address_line1="Test st 1",
            delivery_method=Order.DeliveryMethod.COURIER,
            payment_method=Order.PaymentMethod.CASH,
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            variant=self.variant,
            product_name="Корейский крем",
            sku=self.variant.sku,
            unit_price=self.variant.price,
            quantity=1,
            line_total=self.variant.price,
        )
        order.recalculate_totals(save=True)
        return order


# =============================================================================
# 1.  CHECKOUT  POST /api/v1/orders/checkout/
# =============================================================================

class TestCheckout(OrdersBaseTest):

    def test_checkout_success_creates_order(self):
        """Happy path: creates an Order with status=pending."""
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_checkout_creates_order_items_with_snapshot(self):
        """OrderItem snapshot must contain product_name, sku, unit_price."""
        self.checkout()
        item = OrderItem.objects.first()
        self.assertIsNotNone(item)
        self.assertEqual(item.sku, self.variant.sku)
        self.assertEqual(item.unit_price, self.variant.price)
        self.assertEqual(item.product_name, "Корейский крем")

    def test_checkout_deducts_stock(self):
        """Stock of each variant is reduced by the ordered quantity."""
        original_stock = self.variant.stock
        self.checkout()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, original_stock - self.cart_item.quantity)

    def test_checkout_clears_cart(self):
        """Cart is emptied after a successful checkout."""
        self.checkout()
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_checkout_empty_cart_returns_400(self):
        """Checkout with an empty cart returns 400."""
        self.cart.items.all().delete()
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_no_cart_returns_400(self):
        """Checkout when the user has no cart at all returns 400."""
        self.cart.delete()
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_inactive_variant_returns_400(self):
        """Cart item whose variant is inactive → 400 with errors list."""
        self.variant.is_active = False
        self.variant.save()
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_inactive_product_returns_400(self):
        """Cart item whose product is inactive → 400."""
        self.product.is_active = False
        self.product.save()
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_insufficient_stock_returns_400(self):
        """Ordered quantity exceeds available stock → 400 with stock error."""
        self.cart_item.quantity = self.variant.stock + 5
        self.cart_item.save()
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # stock error should mention the sku
        error_text = str(res.data)
        self.assertIn(self.variant.sku, error_text)

    def test_checkout_missing_required_fields_returns_400(self):
        """Missing required fields returns 400 validation error."""
        res = self.client.post(CHECKOUT_URL, {"first_name": "Only"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_invalid_delivery_method_returns_400(self):
        """Invalid delivery_method value → 400."""
        payload = {**VALID_CHECKOUT_PAYLOAD, "delivery_method": "teleport"}
        res = self.checkout(payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_invalid_payment_method_returns_400(self):
        """Invalid payment_method value → 400."""
        payload = {**VALID_CHECKOUT_PAYLOAD, "payment_method": "bitcoin"}
        res = self.checkout(payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_requires_auth(self):
        """Unauthenticated request → 401."""
        self.client.force_authenticate(user=None)
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checkout_order_number_format(self):
        """Order number follows ORD-YYYYMMDD-XXXXXX format."""
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order_number = res.data["order_number"]
        self.assertRegex(order_number, r"^ORD-\d{8}-\d{6}$")

    def test_checkout_response_contains_items(self):
        """Response body includes items list with correct fields."""
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("items", res.data)
        self.assertEqual(len(res.data["items"]), 1)
        item = res.data["items"][0]
        self.assertIn("product_name", item)
        self.assertIn("sku", item)
        self.assertIn("unit_price", item)
        self.assertIn("line_total", item)


# =============================================================================
# 2.  ORDER LIST  GET /api/v1/orders/
# =============================================================================

class TestMyOrderList(OrdersBaseTest):

    def test_list_returns_only_own_orders(self):
        """User sees only their own orders, not orders of other users."""
        other_user = make_user("other@test.com")
        own_order = self._make_order()            # own — created first
        self._make_order(user=other_user)         # foreign

        res = self.get_list()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        # Only the own order should be returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["order_number"], own_order.order_number)

    def test_list_returns_200_when_no_orders(self):
        """Empty list is returned as 200 with zero results, not 404."""
        res = self.get_list()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 0)

    def test_list_requires_auth(self):
        """Unauthenticated request → 401."""
        self.client.force_authenticate(user=None)
        res = self.get_list()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_filter_by_status(self):
        """?status=pending filters correctly."""
        self._make_order(status=Order.Status.PENDING)
        self._make_order(status=Order.Status.DELIVERED)
        res = self.get_list("?status=pending")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "pending")

    def test_list_filter_by_payment_status(self):
        """?payment_status=paid filters correctly."""
        order = self._make_order()
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["payment_status", "updated_at"])

        self._make_order()  # unpaid order

        res = self.get_list("?payment_status=paid")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["payment_status"], "paid")

    def test_list_order_number_in_response(self):
        """Each order in list has an order_number and status field."""
        self._make_order()
        res = self.get_list()
        results = res.data.get("results", res.data)
        self.assertIn("order_number", results[0])
        self.assertIn("status", results[0])


# =============================================================================
# 3.  ORDER DETAIL  GET /api/v1/orders/{id}/
# =============================================================================

class TestMyOrderDetail(OrdersBaseTest):

    def setUp(self):
        super().setUp()
        self.order = self._make_order()

    def test_detail_returns_full_order(self):
        """Detail endpoint returns 200 with all key fields."""
        res = self.get_detail(self.order.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for field in ("order_number", "status", "payment_status", "total_amount"):
            self.assertIn(field, res.data)

    def test_detail_contains_items(self):
        """items list is embedded in the detail response."""
        res = self.get_detail(self.order.pk)
        self.assertIn("items", res.data)
        self.assertEqual(len(res.data["items"]), 1)

    def test_detail_computed_properties(self):
        """full_name and full_address computed fields are present."""
        res = self.get_detail(self.order.pk)
        self.assertIn("full_name", res.data)
        self.assertIn("full_address", res.data)

    def test_detail_requires_auth(self):
        """Unauthenticated request → 401."""
        self.client.force_authenticate(user=None)
        res = self.get_detail(self.order.pk)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_own_order_returns_200(self):
        """Owner can access their own order."""
        res = self.get_detail(self.order.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_detail_other_user_order_returns_404(self):
        """Another user cannot see someone else's order — returns 404."""
        other = make_user("spy@test.com")
        self.client.force_authenticate(user=other)
        res = self.get_detail(self.order.pk)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_nonexistent_returns_404(self):
        """Non-existent order ID → 404."""
        res = self.get_detail(99999)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# 4.  CANCEL  POST /api/v1/orders/{id}/cancel/
# =============================================================================

class TestCancelOrder(OrdersBaseTest):

    def test_cancel_pending_order_success(self):
        """PENDING order can be canceled → 200, status becomes 'canceled'."""
        order = self._make_order(status=Order.Status.PENDING)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.Status.CANCELED)

    def test_cancel_confirmed_order_success(self):
        """CONFIRMED order can also be canceled by customer."""
        order = self._make_order(status=Order.Status.CONFIRMED)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Order.Status.CANCELED)

    def test_cancel_restores_stock(self):
        """Canceling returns stock for each OrderItem to ProductVariant."""
        original_stock = self.variant.stock
        order = self._make_order(status=Order.Status.PENDING)
        ordered_qty = order.items.first().quantity

        self.cancel(order.pk)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, original_stock + ordered_qty)

    def test_cancel_creates_status_history(self):
        """A status history record is created on cancel."""
        order = self._make_order(status=Order.Status.PENDING)
        self.cancel(order.pk)
        history = OrderStatusHistory.objects.filter(order=order)
        self.assertTrue(history.exists())
        entry = history.first()
        self.assertEqual(entry.new_status, Order.Status.CANCELED)

    def test_cancel_shipped_order_returns_400(self):
        """SHIPPED order cannot be canceled → 400."""
        order = self._make_order(status=Order.Status.SHIPPED)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_cancel_delivered_order_returns_400(self):
        """DELIVERED order cannot be canceled → 400."""
        order = self._make_order(status=Order.Status.DELIVERED)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_other_user_order_returns_404(self):
        """User cannot cancel another user's order → 404."""
        other = make_user("another@test.com")
        order = self._make_order(user=other, status=Order.Status.PENDING)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_already_canceled_returns_400(self):
        """Already CANCELED order cannot be canceled again → 400."""
        order = self._make_order(status=Order.Status.CANCELED)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_requires_auth(self):
        """Unauthenticated cancel request → 401."""
        order = self._make_order()
        self.client.force_authenticate(user=None)
        res = self.cancel(order.pk)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_with_reason_stored_in_history(self):
        """Cancel reason is stored in OrderStatusHistory.comment."""
        order = self._make_order(status=Order.Status.PENDING)
        reason = "Передумал покупать"
        self.cancel(order.pk, {"reason": reason})
        history = OrderStatusHistory.objects.filter(order=order).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.comment, reason)


# =============================================================================
# 5.  SERVICE UNIT TESTS
# =============================================================================

class TestOrderServices(OrdersBaseTest):

    def test_service_update_order_status_records_history(self):
        """update_order_status() creates an OrderStatusHistory entry."""
        order = self._make_order(status=Order.Status.PENDING)
        update_order_status(
            order=order,
            new_status=Order.Status.SHIPPED,
            comment="Shipped via courier",
            changed_by=self.user,
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)

        history = OrderStatusHistory.objects.filter(order=order).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.old_status, Order.Status.PENDING)
        self.assertEqual(history.new_status, Order.Status.SHIPPED)
        self.assertEqual(history.comment, "Shipped via courier")

    def test_service_update_payment_status_auto_confirms(self):
        """
        update_payment_status() with PAID auto-confirms a PENDING order
        and sets the paid_at timestamp.
        """
        order = self._make_order(status=Order.Status.PENDING)
        self.assertIsNone(order.paid_at)

        update_payment_status(
            order=order,
            new_payment_status=Order.PaymentStatus.PAID,
            changed_by=self.user,
        )
        order.refresh_from_db()

        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertIsNotNone(order.paid_at)


# =============================================================================
# 6.  EDGE CASE: Atomicity of checkout
# =============================================================================

class TestCheckoutAtomicity(OrdersBaseTest):
    """If any cart item is invalid, the entire checkout must be rolled back."""

    def setUp(self):
        super().setUp()
        # Add a second item with stock=1 but we'll request 999
        CartItem.objects.create(
            cart=self.cart, variant=self.variant2, quantity=999
        )

    def test_checkout_atomicity_no_order_created(self):
        """When one item fails stock check, no Order row must be created."""
        res = self.checkout()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_atomicity_no_order_items_created(self):
        """No OrderItem row must be created on partial failure."""
        self.checkout()
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_checkout_atomicity_stock_not_deducted(self):
        """Stock of the valid variant must NOT be reduced on failure."""
        original = self.variant.stock
        self.checkout()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, original)

    def test_checkout_atomicity_cart_not_cleared(self):
        """Cart must remain intact when checkout fails."""
        self.checkout()
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 2)


# =============================================================================
# 7.  EDGE CASE: Multi-item checkout totals
# =============================================================================

class TestCheckoutMultiItemTotals(OrdersBaseTest):
    """Checkout with two distinct variants produces correct totals."""

    def setUp(self):
        super().setUp()
        # cart_item (V-001): price=5000 × qty=2  → 10000
        # add V-002:          price=2000 × qty=3  → 6000
        # subtotal = 16000
        CartItem.objects.create(
            cart=self.cart, variant=self.variant2, quantity=3
        )

    def test_multi_item_creates_two_order_items(self):
        """Each cart item becomes a distinct OrderItem."""
        self.checkout()
        self.assertEqual(OrderItem.objects.count(), 2)

    def test_multi_item_subtotal_is_sum_of_line_totals(self):
        """subtotal == sum of all line_total values."""
        self.checkout()
        order = Order.objects.get(user=self.user)
        expected_subtotal = Decimal("5000.00") * 2 + Decimal("2000.00") * 3
        self.assertEqual(order.subtotal, expected_subtotal)

    def test_multi_item_total_amount_equals_subtotal_plus_shipping_minus_discount(self):
        """
        total_amount == subtotal + shipping_cost - discount_amount.
        With no shipping/discount set, total_amount == subtotal.
        """
        self.checkout()
        order = Order.objects.get(user=self.user)
        self.assertEqual(
            order.total_amount,
            order.subtotal + order.shipping_cost - order.discount_amount,
        )

    def test_multi_item_stock_deducted_for_each_variant(self):
        """Each variant's stock is reduced by its ordered quantity."""
        v1_orig = self.variant.stock
        v2_orig = self.variant2.stock
        self.checkout()
        self.variant.refresh_from_db()
        self.variant2.refresh_from_db()
        self.assertEqual(self.variant.stock, v1_orig - 2)
        self.assertEqual(self.variant2.stock, v2_orig - 3)


# =============================================================================
# 8.  EDGE CASE: Snapshot immutability
# =============================================================================

class TestOrderItemSnapshotImmutability(OrdersBaseTest):
    """Changes to variant/product AFTER checkout must not affect OrderItem snapshot."""

    def test_snapshot_preserved_after_sku_change(self):
        """Changing variant.sku after checkout does not update OrderItem.sku."""
        self.checkout()
        order = Order.objects.get(user=self.user)
        original_sku = self.variant.sku

        self.variant.sku = "CHANGED-SKU"
        self.variant.save()

        item = order.items.first()
        self.assertEqual(item.sku, original_sku)

    def test_snapshot_preserved_after_price_change(self):
        """Changing variant.price after checkout does not update OrderItem.unit_price."""
        self.checkout()
        order = Order.objects.get(user=self.user)
        original_price = self.variant.price

        self.variant.price = Decimal("99999.00")
        self.variant.save()

        item = order.items.first()
        self.assertEqual(item.unit_price, original_price)

    def test_snapshot_preserved_after_product_name_change(self):
        """Changing ProductTranslation.name after checkout does not update OrderItem.product_name."""
        self.checkout()
        order = Order.objects.get(user=self.user)
        item = order.items.first()
        original_name = item.product_name

        translation = self.product.translations.get(language="ru")
        translation.name = "Полностью другое имя"
        translation.save()

        item.refresh_from_db()
        self.assertEqual(item.product_name, original_name)


# =============================================================================
# 9.  EDGE CASE: Double-cancel does not restore stock twice
# =============================================================================

class TestCancelIdempotency(OrdersBaseTest):

    def test_second_cancel_does_not_restore_stock_again(self):
        """
        After a successful cancel the stock is restored once.
        A second cancel attempt must be rejected (400) and stock must NOT
        be incremented a second time.
        """
        order = self._make_order(status=Order.Status.PENDING)
        ordered_qty = order.items.first().quantity
        original_stock = self.variant.stock

        # First cancel — should succeed
        res1 = self.cancel(order.pk)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        self.variant.refresh_from_db()
        stock_after_first_cancel = self.variant.stock
        self.assertEqual(stock_after_first_cancel, original_stock + ordered_qty)

        # Second cancel — must be rejected
        res2 = self.cancel(order.pk)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        # Stock must not have changed further
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, stock_after_first_cancel)


# =============================================================================
# 10. EDGE CASE: Payment status edge cases
# =============================================================================

class TestPaymentStatusEdgeCases(OrdersBaseTest):

    def test_failed_payment_does_not_auto_confirm(self):
        """Setting payment_status=FAILED must NOT change order status to CONFIRMED."""
        order = self._make_order(status=Order.Status.PENDING)
        update_payment_status(
            order=order,
            new_payment_status=Order.PaymentStatus.FAILED,
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)

    def test_refunded_payment_does_not_auto_confirm(self):
        """Setting payment_status=REFUNDED must NOT change order status."""
        order = self._make_order(status=Order.Status.DELIVERED)
        update_payment_status(
            order=order,
            new_payment_status=Order.PaymentStatus.REFUNDED,
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)

    def test_paid_on_already_confirmed_order_does_not_break_status(self):
        """PAID on a CONFIRMED order must not regress status to PENDING."""
        order = self._make_order(status=Order.Status.CONFIRMED)
        update_payment_status(
            order=order,
            new_payment_status=Order.PaymentStatus.PAID,
        )
        order.refresh_from_db()
        # Status stays CONFIRMED (auto-confirm only fires on PENDING)
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)

    def test_second_paid_call_does_not_overwrite_paid_at(self):
        """
        Calling update_payment_status with PAID a second time (same status)
        must be a no-op — paid_at must not be changed.
        """
        order = self._make_order(status=Order.Status.PENDING)
        update_payment_status(order=order, new_payment_status=Order.PaymentStatus.PAID)
        order.refresh_from_db()
        first_paid_at = order.paid_at

        # Second call with the same status → service returns early
        update_payment_status(order=order, new_payment_status=Order.PaymentStatus.PAID)
        order.refresh_from_db()
        self.assertEqual(order.paid_at, first_paid_at)


# =============================================================================
# 11. EDGE CASE: Status timestamp fields
# =============================================================================

class TestStatusTimestamps(OrdersBaseTest):

    def test_confirmed_at_set_when_status_becomes_confirmed(self):
        """confirmed_at is auto-populated when status changes to CONFIRMED."""
        order = self._make_order(status=Order.Status.PENDING)
        update_order_status(order=order, new_status=Order.Status.CONFIRMED)
        order.refresh_from_db()
        self.assertIsNotNone(order.confirmed_at)

    def test_shipped_at_set_when_status_becomes_shipped(self):
        """shipped_at is auto-populated when status changes to SHIPPED."""
        order = self._make_order(status=Order.Status.CONFIRMED)
        update_order_status(order=order, new_status=Order.Status.SHIPPED)
        order.refresh_from_db()
        self.assertIsNotNone(order.shipped_at)

    def test_delivered_at_set_when_status_becomes_delivered(self):
        """delivered_at is auto-populated when status changes to DELIVERED."""
        order = self._make_order(status=Order.Status.SHIPPED)
        update_order_status(order=order, new_status=Order.Status.DELIVERED)
        order.refresh_from_db()
        self.assertIsNotNone(order.delivered_at)

    def test_canceled_at_set_on_cancel_via_api(self):
        """canceled_at is auto-populated when customer cancels via API."""
        order = self._make_order(status=Order.Status.PENDING)
        self.cancel(order.pk)
        order.refresh_from_db()
        self.assertIsNotNone(order.canceled_at)

    def test_paid_at_set_when_payment_becomes_paid(self):
        """paid_at is auto-populated when payment_status changes to PAID."""
        order = self._make_order(status=Order.Status.PENDING)
        update_payment_status(order=order, new_payment_status=Order.PaymentStatus.PAID)
        order.refresh_from_db()
        self.assertIsNotNone(order.paid_at)


# =============================================================================
# 12. EDGE CASE: Filter edge cases
# =============================================================================

class TestListFilterEdgeCases(OrdersBaseTest):

    def test_filter_status_no_match_returns_empty_200(self):
        """?status=refunded with no matching orders → 200 with empty list."""
        self._make_order(status=Order.Status.PENDING)
        res = self.get_list("?status=refunded")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 0)

    def test_filter_invalid_status_value_returns_empty_200(self):
        """
        ?status=abracadabra matches nothing → 200 with empty list.
        Behaviour is preserved as a regression guard.
        """
        self._make_order()
        res = self.get_list("?status=abracadabra")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 0)


# =============================================================================
# 13. EDGE CASE: Money field serialization format
# =============================================================================

class TestMoneyFieldFormat(OrdersBaseTest):

    def test_total_amount_serialized_as_decimal_string(self):
        """
        DRF serializes Decimal fields as strings with two decimal places.
        Frontend depends on "5000.00", not 5000 or 5000.0.
        """
        self.checkout()
        order = Order.objects.get(user=self.user)
        res = self.get_detail(order.pk)
        self.assertRegex(res.data["total_amount"], r"^\d+\.\d{2}$")
        self.assertRegex(res.data["subtotal"], r"^\d+\.\d{2}$")
        self.assertRegex(res.data["shipping_cost"], r"^\d+\.\d{2}$")
        self.assertRegex(res.data["discount_amount"], r"^\d+\.\d{2}$")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for pickup tests
# ─────────────────────────────────────────────────────────────────────────────

def make_pickup_location(
    city="Bishkek",
    name="Main Office",
    address="Chui Ave 100",
    is_active=True,
    sort_order=0,
):
    """Factory helper to create a PickupLocation instance."""
    return PickupLocation.objects.create(
        city=city,
        name=name,
        address=address,
        is_active=is_active,
        sort_order=sort_order,
    )


PICKUP_CHECKOUT_PAYLOAD = {
    "customer_phone": "+996700000001",
    "first_name": "Адиль",
    "delivery_method": "pickup",
    "payment_method": "cash",
    # pickup_location_id injected in each test
}


# =============================================================================
# 14.  PICKUP LOCATION LIST
# =============================================================================

class TestPickupLocationList(OrdersBaseTest):
    """GET /api/v1/orders/pickup-locations/"""

    def test_list_returns_200(self):
        """Returns 200 with active locations."""
        make_pickup_location(name="Point A")
        res = self.client.get(PICKUP_LOCATIONS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_list_returns_active_locations_only(self):
        """Inactive locations are excluded from the response."""
        active = make_pickup_location(name="Active", is_active=True)
        make_pickup_location(name="Inactive", is_active=False)
        res = self.client.get(PICKUP_LOCATIONS_URL)
        results = res.data.get("results", res.data)
        names = [r["name"] for r in results]
        self.assertIn(active.name, names)
        self.assertNotIn("Inactive", names)

    def test_list_excludes_inactive_entirely(self):
        """Response count matches only active locations."""
        make_pickup_location(is_active=True)
        make_pickup_location(name="Off", is_active=False)
        res = self.client.get(PICKUP_LOCATIONS_URL)
        results = res.data.get("results", res.data)
        self.assertEqual(len(results), 1)

    def test_list_requires_auth(self):
        """Unauthenticated request → 401."""
        self.client.force_authenticate(user=None)
        res = self.client.get(PICKUP_LOCATIONS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_contains_expected_fields(self):
        """Each location object has id, city, name, address, lat/lon, phone, working_hours."""
        make_pickup_location(name="Central")
        res = self.client.get(PICKUP_LOCATIONS_URL)
        results = res.data.get("results", res.data)
        expected_keys = {"id", "city", "name", "address", "latitude", "longitude",
                         "phone", "working_hours"}
        self.assertTrue(expected_keys.issubset(results[0].keys()))


# =============================================================================
# 15.  CHECKOUT WITH PICKUP
# =============================================================================

class TestCheckoutPickup(OrdersBaseTest):
    """Checkout edge cases specific to delivery_method=pickup."""

    def setUp(self):
        super().setUp()
        self.pickup = make_pickup_location()

    def _pickup_payload(self, location_id=None):
        payload = {**PICKUP_CHECKOUT_PAYLOAD}
        if location_id is not None:
            payload["pickup_location_id"] = location_id
        return payload

    def test_pickup_without_location_returns_400(self):
        """delivery_method=pickup without pickup_location_id → 400."""
        res = self.checkout(self._pickup_payload())
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pickup_location_id", str(res.data))

    def test_pickup_with_valid_location_returns_201(self):
        """delivery_method=pickup with valid active location → 201."""
        res = self.checkout(self._pickup_payload(self.pickup.pk))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_pickup_order_has_correct_delivery_method(self):
        """Created order carries delivery_method=pickup."""
        self.checkout(self._pickup_payload(self.pickup.pk))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.delivery_method, Order.DeliveryMethod.PICKUP)

    def test_pickup_snapshots_location_name(self):
        """pickup_location_name on Order matches the chosen location’s name."""
        self.checkout(self._pickup_payload(self.pickup.pk))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.pickup_location_name, self.pickup.name)

    def test_pickup_snapshots_location_city(self):
        """pickup_city on Order matches the chosen location’s city."""
        self.checkout(self._pickup_payload(self.pickup.pk))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.pickup_city, self.pickup.city)

    def test_pickup_snapshots_location_address(self):
        """pickup_address on Order matches the chosen location’s address."""
        self.checkout(self._pickup_payload(self.pickup.pk))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.pickup_address, self.pickup.address)

    def test_courier_with_pickup_location_returns_400(self):
        """delivery_method=courier + pickup_location_id provided → 400."""
        payload = {
            **VALID_CHECKOUT_PAYLOAD,
            "pickup_location_id": self.pickup.pk,
        }
        res = self.checkout(payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pickup_location_id", str(res.data))

    def test_pickup_with_inactive_location_returns_400(self):
        """Inactive pickup location → 400 (not a valid choice)."""
        inactive = make_pickup_location(name="Closed", is_active=False)
        res = self.checkout(self._pickup_payload(inactive.pk))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_courier_without_city_returns_400(self):
        """delivery_method=courier without city → 400."""
        payload = {
            "customer_phone": "+996700000001",
            "first_name": "Адиль",
            "address_line1": "Manas 10",
            "delivery_method": "courier",
            "payment_method": "cash",
            # city intentionally omitted
        }
        res = self.checkout(payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("city", str(res.data))


# =============================================================================
# 16.  PICKUP LOCATION SNAPSHOT IMMUTABILITY
# =============================================================================

class TestPickupLocationSnapshot(OrdersBaseTest):
    """Changing or deleting a PickupLocation after checkout must not update the snapshot."""

    def setUp(self):
        super().setUp()
        self.pickup = make_pickup_location(name="Original Name", city="Bishkek", address="Chui 1")
        payload = {**PICKUP_CHECKOUT_PAYLOAD, "pickup_location_id": self.pickup.pk}
        self.checkout(payload)
        self.order = Order.objects.get(user=self.user)

    def test_snapshot_name_preserved_after_location_rename(self):
        """Renaming a location does not alter order.pickup_location_name."""
        self.pickup.name = "Renamed Location"
        self.pickup.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.pickup_location_name, "Original Name")

    def test_snapshot_address_preserved_after_location_move(self):
        """Changing a location’s address does not alter order.pickup_address."""
        self.pickup.address = "New Address 999"
        self.pickup.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.pickup_address, "Chui 1")

    def test_snapshot_preserved_after_location_deleted(self):
        """
        Deleting the pickup location sets FK to NULL (SET_NULL)
        but snapshot fields remain intact.
        """
        self.pickup.delete()
        self.order.refresh_from_db()
        self.assertIsNone(self.order.pickup_location)  # FK is gone
        self.assertEqual(self.order.pickup_location_name, "Original Name")  # snapshot intact
        self.assertEqual(self.order.pickup_address, "Chui 1")
