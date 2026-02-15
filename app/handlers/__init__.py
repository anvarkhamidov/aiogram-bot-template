from aiogram import Router

from app.handlers.admin import router as admin_router
from app.handlers.cart import router as cart_router
from app.handlers.menu import router as menu_router
from app.handlers.order import router as order_router
from app.handlers.start import router as start_router


def setup_routers() -> Router:
    root_router = Router()
    root_router.include_routers(
        start_router,
        menu_router,
        cart_router,
        order_router,
        admin_router,
    )
    return root_router
