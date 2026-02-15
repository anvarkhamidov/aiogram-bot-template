from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import CartActionCB, cart_keyboard
from app.services.cart import CartService
from app.services.order import OrderService
from app.services.user import UserService

router = Router()


class CheckoutState(StatesGroup):
    address = State()
    phone = State()
    confirm = State()


@router.message(Command("cart"))
async def cmd_cart(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    cart_service = CartService(session)
    items = await cart_service.get_items(user.id)

    if not items:
        await message.answer("Your cart is empty. Use /menu to browse restaurants.")
        return

    total = sum(item.subtotal for item in items)
    text = "<b>Your Cart:</b>\n\n"
    for item in items:
        text += f"  {item.product.name} x{item.quantity} - {item.subtotal / 100:.2f} $\n"
    text += f"\n<b>Total: {total / 100:.2f} $</b>"

    await message.answer(text, reply_markup=cart_keyboard(items))


@router.callback_query(CartActionCB.filter())
async def cart_action(
    callback: CallbackQuery,
    callback_data: CartActionCB,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Please /start the bot first", show_alert=True)
        return

    cart_service = CartService(session)

    if callback_data.action == "remove":
        await cart_service.remove_item(callback_data.item_id)
        items = await cart_service.get_items(user.id)
        if not items:
            await callback.message.edit_text("Your cart is now empty.")
        else:
            total = sum(item.subtotal for item in items)
            text = "<b>Your Cart:</b>\n\n"
            for item in items:
                text += f"  {item.product.name} x{item.quantity} - {item.subtotal / 100:.2f} $\n"
            text += f"\n<b>Total: {total / 100:.2f} $</b>"
            await callback.message.edit_text(text, reply_markup=cart_keyboard(items))
        await callback.answer("Removed")

    elif callback_data.action == "clear":
        await cart_service.clear(user.id)
        await callback.message.edit_text("Cart cleared.")
        await callback.answer()

    elif callback_data.action == "checkout":
        items = await cart_service.get_items(user.id)
        if not items:
            await callback.answer("Cart is empty", show_alert=True)
            return

        if user.delivery_address:
            await state.update_data(address=user.delivery_address)
            if user.phone:
                await state.update_data(phone=user.phone)
                await _show_order_confirmation(callback.message, items, user, state)
                await callback.answer()
                return

        await callback.message.edit_text(
            "Please enter your delivery address:"
        )
        await state.set_state(CheckoutState.address)
        await callback.answer()


@router.message(CheckoutState.address)
async def process_address(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(address=message.text)

    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if user and user.phone:
        await state.update_data(phone=user.phone)
        cart_service = CartService(session)
        items = await cart_service.get_items(user.id)
        await _show_order_confirmation(message, items, user, state)
        return

    await message.answer("Enter your phone number:")
    await state.set_state(CheckoutState.phone)


@router.message(CheckoutState.phone)
async def process_phone(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.update_data(phone=message.text)

    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Error. Please /start the bot.")
        await state.clear()
        return

    cart_service = CartService(session)
    items = await cart_service.get_items(user.id)
    await _show_order_confirmation(message, items, user, state)


async def _show_order_confirmation(message, items, user, state: FSMContext) -> None:
    data = await state.get_data()
    total = sum(item.product.price * item.quantity for item in items)

    text = "<b>Order Summary:</b>\n\n"
    for item in items:
        subtotal = item.product.price * item.quantity
        text += f"  {item.product.name} x{item.quantity} - {subtotal / 100:.2f} $\n"
    text += f"\n<b>Total: {total / 100:.2f} $</b>"
    text += f"\nAddress: {data['address']}"
    text += f"\nPhone: {data['phone']}"
    text += "\n\nSend 'yes' to confirm or 'no' to cancel."

    await message.answer(text)
    await state.set_state(CheckoutState.confirm)


@router.message(CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text and message.text.lower() in ("yes", "da", "confirm"):
        data = await state.get_data()
        user_service = UserService(session)
        user = await user_service.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Error. Please /start the bot.")
            await state.clear()
            return

        await user_service.update_contact(
            message.from_user.id, data["phone"], data["address"]
        )

        cart_service = CartService(session)
        items = await cart_service.get_items(user.id)
        if not items:
            await message.answer("Cart is empty.")
            await state.clear()
            return

        restaurant_id = items[0].product.category.restaurant_id

        order_service = OrderService(session)
        order = await order_service.create_from_cart(
            user_id=user.id,
            restaurant_id=restaurant_id,
            cart_items=items,
            delivery_address=data["address"],
            phone=data["phone"],
        )

        await cart_service.clear(user.id)
        await state.clear()

        await message.answer(
            f"Order #{order.id} placed!\n"
            f"Status: {order.status.value}\n\n"
            "We will notify you when the status changes.\n"
            "Track your order with /orders"
        )
    else:
        await state.clear()
        await message.answer("Order cancelled. Your cart is still saved.\nUse /cart to view it.")
