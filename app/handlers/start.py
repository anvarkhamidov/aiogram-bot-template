from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.webapp import webapp_menu_keyboard
from app.config import settings
from app.services.user import UserService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user_service = UserService(session)
    await user_service.get_or_create(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
    )

    await message.answer(
        f"Welcome to Food Delivery Bot, {message.from_user.first_name}!\n\n"
        "Here you can order food from the best restaurants.\n\n"
        "Commands:\n"
        "/menu - Browse restaurants\n"
        "/cart - View your cart\n"
        "/orders - Your order history\n"
        "/webapp - Open Mini App\n"
        "/help - Help",
        reply_markup=webapp_menu_keyboard(settings.webapp_base_url),
    )


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message, session: AsyncSession) -> None:
    await cmd_start(message, session)
