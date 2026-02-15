from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import (
    AddToCartCB,
    CategoryCB,
    ProductCB,
    RestaurantCB,
    categories_keyboard,
    product_detail_keyboard,
    products_keyboard,
    restaurants_keyboard,
)
from app.services.cart import CartService
from app.services.restaurant import RestaurantService
from app.services.user import UserService

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message, session: AsyncSession) -> None:
    service = RestaurantService(session)
    restaurants = await service.get_all_active()
    if not restaurants:
        await message.answer("No restaurants available at the moment.")
        return
    await message.answer(
        "Choose a restaurant:",
        reply_markup=restaurants_keyboard(restaurants),
    )


@router.callback_query(F.data == "back_restaurants")
async def back_to_restaurants(callback: CallbackQuery, session: AsyncSession) -> None:
    service = RestaurantService(session)
    restaurants = await service.get_all_active()
    if not restaurants:
        await callback.message.edit_text("No restaurants available at the moment.")
        return
    await callback.message.edit_text(
        "Choose a restaurant:",
        reply_markup=restaurants_keyboard(restaurants),
    )
    await callback.answer()


@router.callback_query(RestaurantCB.filter())
async def show_categories(
    callback: CallbackQuery, callback_data: RestaurantCB, session: AsyncSession
) -> None:
    service = RestaurantService(session)
    restaurant = await service.get_by_id(callback_data.id)
    if not restaurant:
        await callback.answer("Restaurant not found", show_alert=True)
        return

    categories = await service.get_menu(callback_data.id)
    if not categories:
        await callback.answer("Menu is empty", show_alert=True)
        return

    text = f"<b>{restaurant.name}</b>\n"
    if restaurant.description:
        text += f"{restaurant.description}\n"
    text += "\nChoose a category:"

    await callback.message.edit_text(
        text,
        reply_markup=categories_keyboard(categories, restaurant.id),
    )
    await callback.answer()


@router.callback_query(CategoryCB.filter())
async def show_products(
    callback: CallbackQuery, callback_data: CategoryCB, session: AsyncSession
) -> None:
    service = RestaurantService(session)
    category_list = await service.get_menu(callback_data.restaurant_id)
    category = None
    for c in category_list:
        if c.id == callback_data.id:
            category = c
            break

    if not category:
        await callback.answer("Category not found", show_alert=True)
        return

    available_products = [p for p in category.products if p.is_available]
    if not available_products:
        await callback.answer("No products available in this category", show_alert=True)
        return

    await callback.message.edit_text(
        f"<b>{category.name}</b>\n\nSelect a dish:",
        reply_markup=products_keyboard(
            available_products, callback_data.restaurant_id, callback_data.id
        ),
    )
    await callback.answer()


@router.callback_query(ProductCB.filter())
async def show_product_detail(
    callback: CallbackQuery, callback_data: ProductCB, session: AsyncSession
) -> None:
    service = RestaurantService(session)
    product = await service.get_product(callback_data.id)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return

    text = f"<b>{product.name}</b>\n"
    if product.description:
        text += f"\n{product.description}\n"
    text += f"\nPrice: <b>{product.price_display} $</b>"

    await callback.message.edit_text(
        text,
        reply_markup=product_detail_keyboard(product),
    )
    await callback.answer()


@router.callback_query(AddToCartCB.filter())
async def add_to_cart(
    callback: CallbackQuery, callback_data: AddToCartCB, session: AsyncSession
) -> None:
    user_service = UserService(session)
    user = await user_service.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Please /start the bot first", show_alert=True)
        return

    cart_service = CartService(session)
    await cart_service.add_item(user.id, callback_data.product_id)
    await callback.answer("Added to cart!", show_alert=False)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()
