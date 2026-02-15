from app.models.cart import CartItem
from app.models.category import Category
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User


async def test_create_user(session):
    user = User(telegram_id=123456, first_name="John", last_name="Doe", username="johndoe")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 123456
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.username == "johndoe"
    assert user.phone is None
    assert user.delivery_address is None


async def test_create_restaurant(session):
    restaurant = Restaurant(name="Test Place", description="A test restaurant", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    assert restaurant.id is not None
    assert restaurant.name == "Test Place"
    assert restaurant.is_active is True


async def test_create_category_and_products(session):
    restaurant = Restaurant(name="R1", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    category = Category(name="Pizza", restaurant_id=restaurant.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)

    product = Product(
        name="Margherita", price=999, category_id=category.id, description="Classic pizza"
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    assert product.name == "Margherita"
    assert product.price == 999
    assert product.price_display == "9.99"
    assert product.is_available is True
    assert product.category_id == category.id


async def test_cart_item_subtotal(session):
    restaurant = Restaurant(name="R1", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    category = Category(name="Cat", restaurant_id=restaurant.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)

    product = Product(name="Item", price=500, category_id=category.id)
    session.add(product)
    await session.commit()
    await session.refresh(product)

    user = User(telegram_id=111, first_name="Test")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=3)
    session.add(cart_item)
    await session.commit()
    await session.refresh(cart_item)

    assert cart_item.subtotal == 1500


async def test_order_status_enum():
    assert OrderStatus.PENDING.value == "pending"
    assert OrderStatus.CONFIRMED.value == "confirmed"
    assert OrderStatus.PREPARING.value == "preparing"
    assert OrderStatus.DELIVERING.value == "delivering"
    assert OrderStatus.DELIVERED.value == "delivered"
    assert OrderStatus.CANCELLED.value == "cancelled"


async def test_order_total_display(session):
    restaurant = Restaurant(name="R1", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    user = User(telegram_id=222, first_name="Test")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    order = Order(
        user_id=user.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.PENDING,
        total=2599,
        delivery_address="123 Test St",
        phone="+1234567890",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    assert order.total_display == "25.99"
    assert order.status == OrderStatus.PENDING


async def test_order_item_subtotal(session):
    restaurant = Restaurant(name="R1", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    user = User(telegram_id=333, first_name="Test")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    category = Category(name="Cat", restaurant_id=restaurant.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)

    product = Product(name="Item", price=1000, category_id=category.id)
    session.add(product)
    await session.commit()
    await session.refresh(product)

    order = Order(
        user_id=user.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.PENDING,
        total=2000,
        delivery_address="Addr",
        phone="123",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)

    order_item = OrderItem(
        order_id=order.id, product_id=product.id, quantity=2, price=1000
    )
    session.add(order_item)
    await session.commit()
    await session.refresh(order_item)

    assert order_item.subtotal == 2000


async def test_user_repr(session):
    user = User(telegram_id=999, first_name="Alice")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    assert "Alice" in repr(user)
    assert "999" in repr(user)


async def test_product_availability_default(session):
    restaurant = Restaurant(name="R1", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    category = Category(name="C", restaurant_id=restaurant.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)

    product = Product(name="P", price=100, category_id=category.id)
    session.add(product)
    await session.commit()
    await session.refresh(product)

    assert product.is_available is True
