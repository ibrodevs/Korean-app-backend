"""
Cart API Tests
=============
Coverage:
  - GET  /cart/                       (4 tests)
  - POST /cart/items/                 (5 tests)
  - PATCH /cart/items/<id>/           (5 tests)
  - DELETE /cart/items/<id>/          (3 tests)
  - DELETE /cart/clear/               (2 tests)
  - POST /cart/items/bulk-add/        (4 tests)
  - PATCH /cart/items/bulk-update/    (3 tests)
  - DELETE /cart/items/bulk-delete/   (3 tests)

Total: 29 tests
"""
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from core.models import CustomUser, Cart, CartItem
from products.models import Category, Product, ProductVariant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email="user@test.com", password="Test1234"):
    return CustomUser.objects.create_user(email=email, password=password)


def make_product(slug="test-product", is_active=True):
    category, _ = Category.objects.get_or_create(slug="test-cat")
    return Product.objects.create(
        category=category,
        slug=slug,
        is_active=is_active,
        min_price=Decimal("1000.00"),
    )


def make_variant(product, sku="SKU-001", price="1000.00", stock=10, is_active=True):
    return ProductVariant.objects.create(
        product=product,
        sku=sku,
        price=Decimal(price),
        stock=stock,
        is_active=is_active,
    )


# ---------------------------------------------------------------------------
# Base class with common setUp
# ---------------------------------------------------------------------------

class CartBaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

        self.product = make_product()
        self.variant = make_variant(self.product, sku="V-001", stock=10)
        self.variant2 = make_variant(self.product, sku="V-002", stock=5)

    # Shortcuts
    def get_cart(self):
        return self.client.get("/api/auth/cart/")

    def add_item(self, variant_id, quantity=1):
        return self.client.post("/api/auth/cart/items/", {"variant_id": variant_id, "quantity": quantity}, format="json")

    def update_item(self, item_id, quantity):
        return self.client.patch(f"/api/auth/cart/items/{item_id}/", {"quantity": quantity}, format="json")

    def delete_item(self, item_id):
        return self.client.delete(f"/api/auth/cart/items/{item_id}/")

    def clear_cart(self):
        return self.client.delete("/api/auth/cart/clear/")


# ===========================================================================
# 1. GET /cart/ — получить корзину
# ===========================================================================

class TestGetCart(CartBaseTest):

    def test_get_cart_returns_200(self):
        """Авторизованный пользователь получает пустую корзину."""
        res = self.get_cart()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("items", res.data)
        self.assertEqual(res.data["total_items"], 0)
        self.assertEqual(res.data["total_quantity"], 0)

    def test_get_cart_creates_if_not_exists(self):
        """Корзина создаётся автоматически при первом запросе."""
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        self.get_cart()
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_get_cart_requires_auth(self):
        """Неавторизованный пользователь получает 401."""
        self.client.force_authenticate(user=None)
        res = self.get_cart()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_cart_shows_existing_items(self):
        """Корзина содержит ранее добавленный товар с верными полями."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=3)

        res = self.get_cart()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 1)
        self.assertEqual(res.data["total_quantity"], 3)
        item = res.data["items"][0]
        self.assertEqual(item["quantity"], 3)
        self.assertEqual(item["sku"], self.variant.sku)


# ===========================================================================
# 2. POST /cart/items/ — добавить товар
# ===========================================================================

class TestAddCartItem(CartBaseTest):

    def test_add_item_success_returns_cart(self):
        """Добавление товара возвращает обновлённую корзину (201)."""
        res = self.add_item(self.variant.id, quantity=2)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["total_items"], 1)
        self.assertEqual(res.data["total_quantity"], 2)

    def test_add_item_accumulates_quantity(self):
        """Повторное добавление того же варианта суммирует количество."""
        self.add_item(self.variant.id, quantity=2)
        res = self.add_item(self.variant.id, quantity=3)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["total_quantity"], 5)

    def test_add_item_nonexistent_variant_returns_400(self):
        """Несуществующий variant_id → 400 с понятным сообщением."""
        res = self.add_item(variant_id=99999)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Ошибка валидации сериализатора содержит detail об отсутствии варианта
        error_text = str(res.data)
        self.assertIn("variant_id", error_text.lower() + "вариант товара не найден".lower())

    def test_add_item_inactive_variant_returns_400(self):
        """Неактивный вариант товара → 400."""
        inactive = make_variant(self.product, sku="V-INACTIVE", stock=10, is_active=False)
        res = self.add_item(inactive.id)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_exceeds_stock_returns_400(self):
        """Количество больше остатка на складе → 400."""
        res = self.add_item(self.variant.id, quantity=self.variant.stock + 1)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)
        self.assertIn("складе", res.data["detail"])

    def test_add_item_requires_auth(self):
        """Неавторизованный запрос → 401."""
        self.client.force_authenticate(user=None)
        res = self.add_item(self.variant.id)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================================================================
# 3. PATCH /cart/items/<id>/ — изменить количество
# ===========================================================================

class TestUpdateCartItem(CartBaseTest):

    def setUp(self):
        super().setUp()
        cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)

    def test_update_item_success(self):
        """Обновление количества возвращает корзину с новым количеством (200)."""
        res = self.update_item(self.cart_item.id, quantity=4)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["items"][0]["quantity"], 4)

    def test_update_item_not_found_returns_404(self):
        """Несуществующий item_id → 404 с понятным сообщением."""
        res = self.update_item(item_id=99999, quantity=1)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", res.data)
        self.assertIn("не найден", res.data["detail"])

    def test_update_item_exceeds_stock_returns_400(self):
        """Новое количество больше остатка на складе → 400."""
        res = self.update_item(self.cart_item.id, quantity=self.variant.stock + 100)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("складе", res.data["detail"])

    def test_update_item_zero_quantity_returns_400(self):
        """Quantity=0 не проходит валидацию сериализатора → 400."""
        res = self.update_item(self.cart_item.id, quantity=0)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_item_of_another_user_returns_404(self):
        """Чужой cart item недоступен (ownership check) → 404."""
        other_user = make_user(email="other@test.com")
        self.client.force_authenticate(user=other_user)
        res = self.update_item(self.cart_item.id, quantity=1)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ===========================================================================
# 4. DELETE /cart/items/<id>/ — удалить товар
# ===========================================================================

class TestDeleteCartItem(CartBaseTest):

    def setUp(self):
        super().setUp()
        cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)

    def test_delete_item_success(self):
        """Удаление товара → 200 с пустой корзиной."""
        res = self.delete_item(self.cart_item.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 0)
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    def test_delete_item_not_found_returns_404(self):
        """Несуществующий item_id → 404 с понятным сообщением."""
        res = self.delete_item(item_id=99999)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("не найден", res.data["detail"])

    def test_delete_item_of_another_user_returns_404(self):
        """Попытка удалить чужой товар → 404."""
        other_user = make_user(email="another@test.com")
        self.client.force_authenticate(user=other_user)
        res = self.delete_item(self.cart_item.id)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ===========================================================================
# 5. DELETE /cart/clear/ — очистить корзину
# ===========================================================================

class TestClearCart(CartBaseTest):

    def test_clear_cart_removes_all_items(self):
        """Очистка корзины удаляет все товары и возвращает пустую корзину."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        CartItem.objects.create(cart=cart, variant=self.variant2, quantity=1)

        res = self.clear_cart()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 0)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_clear_cart_no_existing_cart(self):
        """Очистка без существующей корзины не падает — возвращает 200."""
        self.assertFalse(Cart.objects.filter(user=self.user).exists())
        res = self.clear_cart()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 0)


# ===========================================================================
# 6. POST /cart/items/bulk-add/ — массовое добавление
# ===========================================================================

class TestBulkAddCartItems(CartBaseTest):

    def bulk_add(self, items):
        return self.client.post("/api/auth/cart/items/bulk-add/", {"items": items}, format="json")

    def test_bulk_add_success(self):
        """Добавление нескольких товаров одним запросом → 200 с обновлённой корзиной."""
        res = self.bulk_add([
            {"variant_id": self.variant.id, "quantity": 2},
            {"variant_id": self.variant2.id, "quantity": 1},
        ])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 2)
        self.assertEqual(res.data["total_quantity"], 3)

    def test_bulk_add_invalid_variant_returns_400(self):
        """Несуществующий вариант в списке → 400 с указанием variant_id."""
        res = self.bulk_add([
            {"variant_id": self.variant.id, "quantity": 1},
            {"variant_id": 99999, "quantity": 1},
        ])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)
        self.assertIn("99999", res.data["detail"])

    def test_bulk_add_exceeds_stock_returns_400(self):
        """Превышение склада для одного товара в батче → 400."""
        res = self.bulk_add([
            {"variant_id": self.variant.id, "quantity": self.variant.stock + 100},
        ])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("складе", res.data["detail"])

    def test_bulk_add_empty_list_returns_400(self):
        """Пустой список items → 400 с понятным сообщением."""
        res = self.bulk_add([])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ===========================================================================
# 7. PATCH /cart/items/bulk-update/ — массовое обновление
# ===========================================================================

class TestBulkUpdateCartItems(CartBaseTest):

    def setUp(self):
        super().setUp()
        cart = Cart.objects.create(user=self.user)
        self.item1 = CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        self.item2 = CartItem.objects.create(cart=cart, variant=self.variant2, quantity=1)

    def bulk_update(self, items):
        return self.client.patch("/api/auth/cart/items/bulk-update/", {"items": items}, format="json")

    def test_bulk_update_success(self):
        """Обновление нескольких позиций одним запросом → 200."""
        res = self.bulk_update([
            {"item_id": self.item1.id, "quantity": 3},
            {"item_id": self.item2.id, "quantity": 2},
        ])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_quantity"], 5)

    def test_bulk_update_invalid_item_id_returns_400(self):
        """Несуществующий item_id в батче → 400 с указанием ID."""
        res = self.bulk_update([
            {"item_id": 99999, "quantity": 1},
        ])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("99999", res.data["detail"])

    def test_bulk_update_exceeds_stock_returns_400(self):
        """Превышение склада в одной позиции → 400."""
        res = self.bulk_update([
            {"item_id": self.item1.id, "quantity": self.variant.stock + 100},
        ])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("складе", res.data["detail"])


# ===========================================================================
# 8. DELETE /cart/items/bulk-delete/ — массовое удаление
# ===========================================================================

class TestBulkDeleteCartItems(CartBaseTest):

    def setUp(self):
        super().setUp()
        cart = Cart.objects.create(user=self.user)
        self.item1 = CartItem.objects.create(cart=cart, variant=self.variant, quantity=1)
        self.item2 = CartItem.objects.create(cart=cart, variant=self.variant2, quantity=2)

    def bulk_delete(self, item_ids):
        return self.client.delete("/api/auth/cart/items/bulk-delete/", {"item_ids": item_ids}, format="json")

    def test_bulk_delete_success(self):
        """Массовое удаление нескольких позиций → 200 с обновлённой корзиной."""
        res = self.bulk_delete([self.item1.id, self.item2.id])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_items"], 0)
        self.assertFalse(CartItem.objects.filter(id__in=[self.item1.id, self.item2.id]).exists())

    def test_bulk_delete_partial_ids_deletes_only_own(self):
        """
        Удаление по ID чужих товаров игнорируется (ownership через cart=cart),
        свои удаляются корректно.
        """
        other_user = make_user(email="bulk_other@test.com")
        other_cart = Cart.objects.create(user=other_user)
        other_item = CartItem.objects.create(cart=other_cart, variant=self.variant, quantity=1)

        res = self.bulk_delete([self.item1.id, other_item.id])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # self.item1 удалён, other_item — нет (чужой)
        self.assertFalse(CartItem.objects.filter(id=self.item1.id).exists())
        self.assertTrue(CartItem.objects.filter(id=other_item.id).exists())

    def test_bulk_delete_empty_list_returns_400(self):
        """Пустой список item_ids → 400 (allow_empty=False в сериализаторе)."""
        res = self.bulk_delete([])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
