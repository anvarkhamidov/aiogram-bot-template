from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.keyboards.inline import OrderActionCB, admin_order_keyboard
from app.models.order import OrderStatus
from app.services.order import OrderService
from app.services.restaurant import RestaurantService

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    await message.answer(
        "<b>Admin Panel</b>\n\n"
        "/pending - View pending orders\n"
        "/add_restaurant - Add a restaurant\n"
        "/seed - Load sample data"
    )


@router.message(Command("pending"))
async def cmd_pending(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return

    order_service = OrderService(session)
    orders = await order_service.get_all_pending()

    if not orders:
        await message.answer("No pending orders.")
        return

    for order in orders:
        text = (
            f"<b>Order #{order.id}</b>\n"
            f"User: {order.user.first_name} ({order.user.telegram_id})\n"
            f"Address: {order.delivery_address}\n"
            f"Phone: {order.phone}\n"
            f"Total: {order.total_display} $\n\n"
            f"Items:\n"
        )
        for item in order.items:
            text += f"  {item.product.name} x{item.quantity}\n"

        await message.answer(text, reply_markup=admin_order_keyboard(order))


@router.callback_query(OrderActionCB.filter())
async def admin_order_action(
    callback: CallbackQuery, callback_data: OrderActionCB, session: AsyncSession
) -> None:
    if not is_admin(callback.from_user.id):
        return

    action_map = {
        "confirm": OrderStatus.CONFIRMED,
        "prepare": OrderStatus.PREPARING,
        "deliver": OrderStatus.DELIVERING,
        "complete": OrderStatus.DELIVERED,
        "admin_cancel": OrderStatus.CANCELLED,
    }

    new_status = action_map.get(callback_data.action)
    if not new_status:
        return

    order_service = OrderService(session)
    order = await order_service.update_status(callback_data.order_id, new_status)
    if order:
        await callback.message.edit_text(
            f"Order #{order.id} updated to: {order.status.value}"
        )
        await callback.answer(f"Status: {order.status.value}")
    else:
        await callback.answer("Order not found", show_alert=True)


@router.message(Command("seed"))
async def cmd_seed(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return

    service = RestaurantService(session)

    existing = await service.get_all_active()
    if existing:
        await message.answer("Data already loaded. Restaurants exist.")
        return

    r1 = await service.create_restaurant(
        name="Pizza Palace",
        description="Best pizza in town!",
        address="123 Main St",
    )
    cat1 = await service.create_category("Pizza", r1.id)
    cat2 = await service.create_category("Drinks", r1.id)

    await service.create_product("Margherita", 899, cat1.id, "Classic tomato and mozzarella")
    await service.create_product("Pepperoni", 1099, cat1.id, "Spicy pepperoni with cheese")
    await service.create_product("Hawaiian", 1199, cat1.id, "Ham and pineapple")
    await service.create_product("Coca-Cola", 199, cat2.id, "330ml can")
    await service.create_product("Water", 99, cat2.id, "500ml bottle")

    r2 = await service.create_restaurant(
        name="Sushi Star",
        description="Fresh Japanese cuisine",
        address="456 Oak Ave",
    )
    cat3 = await service.create_category("Rolls", r2.id)
    cat4 = await service.create_category("Sashimi", r2.id)

    await service.create_product("California Roll", 1299, cat3.id, "Crab, avocado, cucumber")
    await service.create_product("Spicy Tuna Roll", 1399, cat3.id, "Fresh tuna with spicy sauce")
    await service.create_product("Salmon Sashimi", 1599, cat4.id, "5 pieces of fresh salmon")
    await service.create_product("Tuna Sashimi", 1699, cat4.id, "5 pieces of fresh tuna")

    r3 = await service.create_restaurant(
        name="Burger Barn",
        description="Gourmet burgers and fries",
        address="789 Elm Blvd",
    )
    cat5 = await service.create_category("Burgers", r3.id)
    cat6 = await service.create_category("Sides", r3.id)

    await service.create_product("Classic Burger", 999, cat5.id, "Beef patty with lettuce and tomato")
    await service.create_product("Cheese Burger", 1099, cat5.id, "With cheddar cheese")
    await service.create_product("Bacon Burger", 1299, cat5.id, "Crispy bacon and BBQ sauce")
    await service.create_product("French Fries", 399, cat6.id, "Crispy golden fries")
    await service.create_product("Onion Rings", 499, cat6.id, "Beer-battered onion rings")

    await message.answer(
        "Sample data loaded!\n"
        f"  3 restaurants, multiple categories and products created."
    )
