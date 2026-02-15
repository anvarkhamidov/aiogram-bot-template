from unittest.mock import MagicMock

from app.keyboards.inline import (
    AddToCartCB,
    CartActionCB,
    CategoryCB,
    OrderActionCB,
    OrderCB,
    ProductCB,
    RestaurantCB,
    admin_order_keyboard,
    cart_keyboard,
    categories_keyboard,
    order_detail_keyboard,
    product_detail_keyboard,
    products_keyboard,
    restaurants_keyboard,
)
from app.keyboards.webapp import webapp_menu_keyboard
from app.models.order import OrderStatus


def _mock_restaurant(id=1, name="TestRest"):
    m = MagicMock()
    m.id = id
    m.name = name
    return m


def _mock_category(id=1, name="TestCat", restaurant_id=1):
    m = MagicMock()
    m.id = id
    m.name = name
    m.restaurant_id = restaurant_id
    return m


def _mock_product(id=1, name="TestProd", price=999, price_display="9.99",
                   is_available=True, category_id=1, category=None):
    m = MagicMock()
    m.id = id
    m.name = name
    m.price = price
    m.price_display = price_display
    m.is_available = is_available
    m.category_id = category_id
    m.category = category or _mock_category()
    m.category.restaurant_id = 1
    return m


def _mock_cart_item(id=1, product_name="Item", price_display="5.00", quantity=2):
    m = MagicMock()
    m.id = id
    m.quantity = quantity
    m.product = MagicMock()
    m.product.name = product_name
    m.product.price_display = price_display
    return m


def _mock_order(id=1, status=OrderStatus.PENDING):
    m = MagicMock()
    m.id = id
    m.status = status
    return m


class TestCallbackData:
    def test_restaurant_cb_pack_unpack(self):
        cb = RestaurantCB(id=42)
        packed = cb.pack()
        assert "42" in packed
        unpacked = RestaurantCB.unpack(packed)
        assert unpacked.id == 42

    def test_category_cb(self):
        cb = CategoryCB(id=5, restaurant_id=10)
        packed = cb.pack()
        unpacked = CategoryCB.unpack(packed)
        assert unpacked.id == 5
        assert unpacked.restaurant_id == 10

    def test_product_cb(self):
        cb = ProductCB(id=7)
        unpacked = ProductCB.unpack(cb.pack())
        assert unpacked.id == 7

    def test_add_to_cart_cb(self):
        cb = AddToCartCB(product_id=3)
        unpacked = AddToCartCB.unpack(cb.pack())
        assert unpacked.product_id == 3

    def test_cart_action_cb(self):
        cb = CartActionCB(action="remove", item_id=5)
        unpacked = CartActionCB.unpack(cb.pack())
        assert unpacked.action == "remove"
        assert unpacked.item_id == 5

    def test_order_cb(self):
        cb = OrderCB(id=100)
        unpacked = OrderCB.unpack(cb.pack())
        assert unpacked.id == 100

    def test_order_action_cb(self):
        cb = OrderActionCB(action="cancel", order_id=50)
        unpacked = OrderActionCB.unpack(cb.pack())
        assert unpacked.action == "cancel"
        assert unpacked.order_id == 50


class TestKeyboardBuilders:
    def test_restaurants_keyboard(self):
        restaurants = [_mock_restaurant(1, "R1"), _mock_restaurant(2, "R2")]
        kb = restaurants_keyboard(restaurants)
        assert len(kb.inline_keyboard) == 2
        assert kb.inline_keyboard[0][0].text == "R1"

    def test_restaurants_keyboard_empty(self):
        kb = restaurants_keyboard([])
        assert len(kb.inline_keyboard) == 0

    def test_categories_keyboard(self):
        categories = [_mock_category(1, "Cat1"), _mock_category(2, "Cat2")]
        kb = categories_keyboard(categories, restaurant_id=1)
        # 2 categories + 1 back button
        assert len(kb.inline_keyboard) == 3
        assert "Cat1" in kb.inline_keyboard[0][0].text

    def test_products_keyboard(self):
        products = [_mock_product(1, "P1"), _mock_product(2, "P2", is_available=False)]
        kb = products_keyboard(products, restaurant_id=1, category_id=1)
        # only 1 available product + 1 back button
        assert len(kb.inline_keyboard) == 2

    def test_product_detail_keyboard(self):
        product = _mock_product()
        kb = product_detail_keyboard(product)
        assert len(kb.inline_keyboard) == 2
        assert "Add to cart" in kb.inline_keyboard[0][0].text

    def test_cart_keyboard_with_items(self):
        items = [_mock_cart_item(1), _mock_cart_item(2)]
        kb = cart_keyboard(items)
        # 2 items + checkout/clear row + browse restaurants row
        assert len(kb.inline_keyboard) == 4

    def test_cart_keyboard_empty(self):
        kb = cart_keyboard([])
        # only browse restaurants button
        assert len(kb.inline_keyboard) == 1

    def test_order_detail_keyboard_pending(self):
        order = _mock_order(status=OrderStatus.PENDING)
        kb = order_detail_keyboard(order)
        assert len(kb.inline_keyboard) == 2  # cancel + back

    def test_order_detail_keyboard_confirmed(self):
        order = _mock_order(status=OrderStatus.CONFIRMED)
        kb = order_detail_keyboard(order)
        assert len(kb.inline_keyboard) == 1  # only back

    def test_admin_order_keyboard_pending(self):
        order = _mock_order(status=OrderStatus.PENDING)
        kb = admin_order_keyboard(order)
        assert len(kb.inline_keyboard) == 2  # confirm + cancel

    def test_admin_order_keyboard_delivered(self):
        order = _mock_order(status=OrderStatus.DELIVERED)
        kb = admin_order_keyboard(order)
        assert len(kb.inline_keyboard) == 0

    def test_webapp_menu_keyboard(self):
        kb = webapp_menu_keyboard("https://example.com")
        assert len(kb.inline_keyboard) == 1
        assert kb.inline_keyboard[0][0].web_app is not None
        assert "example.com" in kb.inline_keyboard[0][0].web_app.url
