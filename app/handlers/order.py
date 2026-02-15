from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import OrderActionCB, OrderCB, order_detail_keyboard
from app.models.order import OrderStatus
from app.services.order import OrderService
from app.services.user import UserService

router = Router()

STATUS_LABELS = {
    OrderStatus.PENDING: "Pending",
    OrderStatus.CONFIRMED: "Confirmed",
    OrderStatus.PREPARING: "Preparing",
    OrderStatus.DELIVERING: "Delivering",
    OrderStatus.DELIVERED: "Delivered",
    OrderStatus.CANCELLED: "Cancelled",
}


@router.message(Command("orders"))
async def cmd_orders(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    order_service = OrderService(session)
    orders = await order_service.get_user_orders(user.id)

    if not orders:
        await message.answer("You have no orders yet. Use /menu to browse restaurants.")
        return

    text = "<b>Your Orders:</b>\n\n"
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for order in orders[:10]:
        label = STATUS_LABELS.get(order.status, order.status.value)
        text += (
            f"Order #{order.id} - {label}\n"
            f"  Total: {order.total_display} $\n"
            f"  Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"Order #{order.id} - {label}",
                callback_data=OrderCB(id=order.id).pack(),
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "my_orders")
async def show_orders_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Please /start the bot first", show_alert=True)
        return

    order_service = OrderService(session)
    orders = await order_service.get_user_orders(user.id)

    if not orders:
        await callback.message.edit_text("You have no orders yet.")
        await callback.answer()
        return

    text = "<b>Your Orders:</b>\n\n"
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = []
    for order in orders[:10]:
        label = STATUS_LABELS.get(order.status, order.status.value)
        text += (
            f"Order #{order.id} - {label}\n"
            f"  Total: {order.total_display} $\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"#{order.id} - {label}",
                callback_data=OrderCB(id=order.id).pack(),
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(OrderCB.filter())
async def show_order_detail(
    callback: CallbackQuery, callback_data: OrderCB, session: AsyncSession
) -> None:
    order_service = OrderService(session)
    order = await order_service.get_by_id(callback_data.id)
    if not order:
        await callback.answer("Order not found", show_alert=True)
        return

    label = STATUS_LABELS.get(order.status, order.status.value)
    text = (
        f"<b>Order #{order.id}</b>\n\n"
        f"Status: {order.status_emoji} {label}\n"
        f"Address: {order.delivery_address}\n"
        f"Phone: {order.phone}\n\n"
        f"<b>Items:</b>\n"
    )
    for item in order.items:
        text += f"  {item.product.name} x{item.quantity} - {item.subtotal / 100:.2f} $\n"
    text += f"\n<b>Total: {order.total_display} $</b>"
    if order.comment:
        text += f"\nComment: {order.comment}"

    await callback.message.edit_text(
        text, reply_markup=order_detail_keyboard(order)
    )
    await callback.answer()


@router.callback_query(OrderActionCB.filter())
async def order_action(
    callback: CallbackQuery, callback_data: OrderActionCB, session: AsyncSession
) -> None:
    if callback_data.action == "cancel":
        user_service = UserService(session)
        user = await user_service.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Error", show_alert=True)
            return

        order_service = OrderService(session)
        order = await order_service.cancel(callback_data.order_id, user.id)
        if order:
            await callback.message.edit_text(
                f"Order #{order.id} has been cancelled."
            )
            await callback.answer("Cancelled")
        else:
            await callback.answer("Cannot cancel this order", show_alert=True)
