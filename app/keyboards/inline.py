from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class RestaurantCB(CallbackData, prefix="rest"):
    id: int


class CategoryCB(CallbackData, prefix="cat"):
    id: int
    restaurant_id: int


class ProductCB(CallbackData, prefix="prod"):
    id: int


class AddToCartCB(CallbackData, prefix="add"):
    product_id: int


class CartActionCB(CallbackData, prefix="cart"):
    action: str
    item_id: int = 0


class OrderCB(CallbackData, prefix="order"):
    id: int


class OrderActionCB(CallbackData, prefix="oa"):
    action: str
    order_id: int


def restaurants_keyboard(restaurants) -> InlineKeyboardMarkup:
    buttons = []
    for r in restaurants:
        buttons.append([
            InlineKeyboardButton(
                text=r.name,
                callback_data=RestaurantCB(id=r.id).pack(),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def categories_keyboard(categories, restaurant_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=cat.name,
                callback_data=CategoryCB(id=cat.id, restaurant_id=restaurant_id).pack(),
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="< Back to restaurants", callback_data="back_restaurants")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products, restaurant_id: int, category_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        if p.is_available:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{p.name} - {p.price_display} $",
                    callback_data=ProductCB(id=p.id).pack(),
                )
            ])
    buttons.append([
        InlineKeyboardButton(
            text="< Back to categories",
            callback_data=RestaurantCB(id=restaurant_id).pack(),
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Add to cart",
                callback_data=AddToCartCB(product_id=product.id).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="< Back",
                callback_data=CategoryCB(
                    id=product.category_id,
                    restaurant_id=product.category.restaurant_id,
                ).pack(),
            )
        ],
    ])


def cart_keyboard(cart_items) -> InlineKeyboardMarkup:
    buttons = []
    for item in cart_items:
        buttons.append([
            InlineKeyboardButton(
                text=f"- {item.product.name} x{item.quantity} ({item.product.price_display}$)",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text="X",
                callback_data=CartActionCB(action="remove", item_id=item.id).pack(),
            ),
        ])
    if cart_items:
        buttons.append([
            InlineKeyboardButton(
                text="Checkout",
                callback_data=CartActionCB(action="checkout").pack(),
            ),
            InlineKeyboardButton(
                text="Clear cart",
                callback_data=CartActionCB(action="clear").pack(),
            ),
        ])
    buttons.append([
        InlineKeyboardButton(text="< Browse restaurants", callback_data="back_restaurants")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_keyboard(order) -> InlineKeyboardMarkup:
    buttons = []
    from app.models.order import OrderStatus

    if order.status == OrderStatus.PENDING:
        buttons.append([
            InlineKeyboardButton(
                text="Cancel order",
                callback_data=OrderActionCB(action="cancel", order_id=order.id).pack(),
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="< My orders", callback_data="my_orders")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_order_keyboard(order) -> InlineKeyboardMarkup:
    from app.models.order import OrderStatus

    status_transitions = {
        OrderStatus.PENDING: ("Confirm", "confirm"),
        OrderStatus.CONFIRMED: ("Start preparing", "prepare"),
        OrderStatus.PREPARING: ("Send for delivery", "deliver"),
        OrderStatus.DELIVERING: ("Mark delivered", "complete"),
    }

    buttons = []
    transition = status_transitions.get(order.status)
    if transition:
        label, action = transition
        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=OrderActionCB(action=action, order_id=order.id).pack(),
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text="Cancel",
                callback_data=OrderActionCB(action="admin_cancel", order_id=order.id).pack(),
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
