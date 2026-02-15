import pytest

from app.models.category import Category
from app.models.order import OrderStatus
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User
from app.services.cart import CartService
from app.services.order import OrderService
from app.services.restaurant import RestaurantService
from app.services.user import UserService


@pytest.fixture
async def sample_user(session) -> User:
    service = UserService(session)
    return await service.get_or_create(
        telegram_id=100500, first_name="Test", last_name="User", username="testuser"
    )


@pytest.fixture
async def sample_restaurant(session) -> Restaurant:
    service = RestaurantService(session)
    return await service.create_restaurant(
        name="Test Restaurant", description="Desc", address="Addr"
    )


@pytest.fixture
async def sample_category(session, sample_restaurant) -> Category:
    service = RestaurantService(session)
    return await service.create_category("Pizza", sample_restaurant.id)


@pytest.fixture
async def sample_product(session, sample_category) -> Product:
    service = RestaurantService(session)
    return await service.create_product(
        name="Margherita", price=899, category_id=sample_category.id, description="Classic"
    )


# ---- UserService ----


class TestUserService:
    async def test_get_or_create_new(self, session):
        service = UserService(session)
        user = await service.get_or_create(telegram_id=12345, first_name="Alice")
        assert user.id is not None
        assert user.telegram_id == 12345
        assert user.first_name == "Alice"

    async def test_get_or_create_existing(self, session):
        service = UserService(session)
        user1 = await service.get_or_create(telegram_id=12345, first_name="Alice")
        user2 = await service.get_or_create(telegram_id=12345, first_name="Alice")
        assert user1.id == user2.id

    async def test_get_by_telegram_id(self, session):
        service = UserService(session)
        await service.get_or_create(telegram_id=99999, first_name="Bob")
        user = await service.get_by_telegram_id(99999)
        assert user is not None
        assert user.first_name == "Bob"

    async def test_get_by_telegram_id_not_found(self, session):
        service = UserService(session)
        user = await service.get_by_telegram_id(999)
        assert user is None

    async def test_update_contact(self, session):
        service = UserService(session)
        await service.get_or_create(telegram_id=11111, first_name="Charlie")
        user = await service.update_contact(11111, "+1234567890", "123 Main St")
        assert user is not None
        assert user.phone == "+1234567890"
        assert user.delivery_address == "123 Main St"

    async def test_update_contact_not_found(self, session):
        service = UserService(session)
        result = await service.update_contact(999999, "phone", "addr")
        assert result is None


# ---- RestaurantService ----


class TestRestaurantService:
    async def test_create_restaurant(self, session):
        service = RestaurantService(session)
        r = await service.create_restaurant("Pizza Place", "Best pizza")
        assert r.id is not None
        assert r.name == "Pizza Place"

    async def test_get_all_active(self, session):
        service = RestaurantService(session)
        await service.create_restaurant("Active One")
        r2 = await service.create_restaurant("Inactive One")
        r2.is_active = False
        await session.commit()

        active = await service.get_all_active()
        assert len(active) == 1
        assert active[0].name == "Active One"

    async def test_get_by_id(self, session, sample_restaurant):
        service = RestaurantService(session)
        r = await service.get_by_id(sample_restaurant.id)
        assert r is not None
        assert r.name == sample_restaurant.name

    async def test_get_by_id_not_found(self, session):
        service = RestaurantService(session)
        r = await service.get_by_id(9999)
        assert r is None

    async def test_create_category(self, session, sample_restaurant):
        service = RestaurantService(session)
        cat = await service.create_category("Burgers", sample_restaurant.id)
        assert cat.id is not None
        assert cat.name == "Burgers"

    async def test_get_menu(self, session, sample_restaurant, sample_category, sample_product):
        restaurant_id = sample_restaurant.id
        # Expire all to force fresh load with selectinload
        session.expire_all()
        service = RestaurantService(session)
        menu = await service.get_menu(restaurant_id)
        assert len(menu) == 1
        assert menu[0].name == "Pizza"
        assert len(menu[0].products) == 1

    async def test_get_product(self, session, sample_product):
        service = RestaurantService(session)
        p = await service.get_product(sample_product.id)
        assert p is not None
        assert p.name == "Margherita"

    async def test_get_product_not_found(self, session):
        service = RestaurantService(session)
        p = await service.get_product(9999)
        assert p is None

    async def test_create_product(self, session, sample_category):
        service = RestaurantService(session)
        p = await service.create_product(
            name="Pepperoni", price=1099, category_id=sample_category.id
        )
        assert p.id is not None
        assert p.price == 1099


# ---- CartService ----


class TestCartService:
    async def test_add_item(self, session, sample_user, sample_product):
        service = CartService(session)
        item = await service.add_item(sample_user.id, sample_product.id, 1)
        assert item.quantity == 1
        assert item.product_id == sample_product.id

    async def test_add_item_increases_quantity(self, session, sample_user, sample_product):
        service = CartService(session)
        await service.add_item(sample_user.id, sample_product.id, 1)
        item = await service.add_item(sample_user.id, sample_product.id, 2)
        assert item.quantity == 3

    async def test_get_items(self, session, sample_user, sample_product):
        service = CartService(session)
        await service.add_item(sample_user.id, sample_product.id, 2)
        items = await service.get_items(sample_user.id)
        assert len(items) == 1
        assert items[0].quantity == 2

    async def test_get_items_empty(self, session, sample_user):
        service = CartService(session)
        items = await service.get_items(sample_user.id)
        assert items == []

    async def test_update_quantity(self, session, sample_user, sample_product):
        service = CartService(session)
        item = await service.add_item(sample_user.id, sample_product.id, 1)
        updated = await service.update_quantity(item.id, 5)
        assert updated is not None
        assert updated.quantity == 5

    async def test_update_quantity_to_zero_removes(self, session, sample_user, sample_product):
        service = CartService(session)
        item = await service.add_item(sample_user.id, sample_product.id, 1)
        result = await service.update_quantity(item.id, 0)
        assert result is None
        items = await service.get_items(sample_user.id)
        assert len(items) == 0

    async def test_update_quantity_not_found(self, session):
        service = CartService(session)
        result = await service.update_quantity(9999, 3)
        assert result is None

    async def test_remove_item(self, session, sample_user, sample_product):
        service = CartService(session)
        item = await service.add_item(sample_user.id, sample_product.id, 1)
        result = await service.remove_item(item.id)
        assert result is True
        items = await service.get_items(sample_user.id)
        assert len(items) == 0

    async def test_remove_item_not_found(self, session):
        service = CartService(session)
        result = await service.remove_item(9999)
        assert result is False

    async def test_clear_cart(self, session, sample_user, sample_product):
        service = CartService(session)
        await service.add_item(sample_user.id, sample_product.id, 3)
        await service.clear(sample_user.id)
        items = await service.get_items(sample_user.id)
        assert len(items) == 0

    async def test_get_total(self, session, sample_user, sample_product):
        service = CartService(session)
        await service.add_item(sample_user.id, sample_product.id, 2)
        total = await service.get_total(sample_user.id)
        assert total == 899 * 2

    async def test_get_total_empty(self, session, sample_user):
        service = CartService(session)
        total = await service.get_total(sample_user.id)
        assert total == 0


# ---- OrderService ----


class TestOrderService:
    async def _setup_cart(self, session, user, product):
        cart_service = CartService(session)
        await cart_service.add_item(user.id, product.id, 2)
        return await cart_service.get_items(user.id)

    async def test_create_from_cart(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="123 Test",
            phone="+123",
        )
        assert order.id is not None
        assert order.total == 899 * 2
        assert order.status == OrderStatus.PENDING
        assert len(order.items) == 1

    async def test_get_by_id(self, session, sample_user, sample_restaurant, sample_product):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        fetched = await service.get_by_id(order.id)
        assert fetched is not None
        assert fetched.id == order.id

    async def test_get_by_id_not_found(self, session):
        service = OrderService(session)
        result = await service.get_by_id(9999)
        assert result is None

    async def test_get_user_orders(self, session, sample_user, sample_restaurant, sample_product):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        orders = await service.get_user_orders(sample_user.id)
        assert len(orders) == 1

    async def test_get_active_orders(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        active = await service.get_active_orders(sample_user.id)
        assert len(active) == 1

        await service.update_status(order.id, OrderStatus.DELIVERED)
        active = await service.get_active_orders(sample_user.id)
        assert len(active) == 0

    async def test_update_status(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        updated = await service.update_status(order.id, OrderStatus.CONFIRMED)
        assert updated is not None
        assert updated.status == OrderStatus.CONFIRMED

    async def test_update_status_not_found(self, session):
        service = OrderService(session)
        result = await service.update_status(9999, OrderStatus.CONFIRMED)
        assert result is None

    async def test_cancel_order(self, session, sample_user, sample_restaurant, sample_product):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        cancelled = await service.cancel(order.id, sample_user.id)
        assert cancelled is not None
        assert cancelled.status == OrderStatus.CANCELLED

    async def test_cancel_order_wrong_user(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        result = await service.cancel(order.id, 999999)
        assert result is None

    async def test_cancel_non_pending_order(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        order = await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        await service.update_status(order.id, OrderStatus.CONFIRMED)
        result = await service.cancel(order.id, sample_user.id)
        assert result is None

    async def test_get_all_pending(
        self, session, sample_user, sample_restaurant, sample_product
    ):
        items = await self._setup_cart(session, sample_user, sample_product)
        service = OrderService(session)
        await service.create_from_cart(
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            cart_items=items,
            delivery_address="Addr",
            phone="Phone",
        )
        pending = await service.get_all_pending()
        assert len(pending) == 1
