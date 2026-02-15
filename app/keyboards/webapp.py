from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def webapp_menu_keyboard(base_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Open Food Menu",
                web_app=WebAppInfo(url=f"{base_url}/webapp"),
            )
        ]
    ])
