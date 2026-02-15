"""
Unified startup script for deployment.
Runs both the Telegram bot (polling) and WebApp server (aiohttp) concurrently.
Also seeds sample data on first launch.
"""
import asyncio
import logging
import os

from aiohttp import web

from app.config import settings
from app.models.restaurant import Restaurant
from app.webapp.routes import create_webapp_routes
from database.engine import close_db, create_engine, create_session_factory, init_db

logger = logging.getLogger(__name__)


async def seed_if_empty(session_factory):
    """Seed sample data if the database is empty."""
    from sqlalchemy import select

    from app.models.category import Category
    from app.models.product import Product

    async with session_factory() as session:
        result = await session.execute(select(Restaurant))
        if result.scalars().first():
            logger.info("Database already has data, skipping seed.")
            return

        logger.info("Seeding sample data...")

        r1 = Restaurant(name="Pizza Palace", description="Best pizza in town!", is_active=True)
        session.add(r1)
        await session.flush()
        cat1 = Category(name="Pizza", restaurant_id=r1.id)
        cat2 = Category(name="Drinks", restaurant_id=r1.id)
        session.add_all([cat1, cat2])
        await session.flush()
        session.add_all([
            Product(name="Margherita", price=899, category_id=cat1.id, description="Classic tomato and mozzarella"),
            Product(name="Pepperoni", price=1099, category_id=cat1.id, description="Spicy pepperoni with cheese"),
            Product(name="Hawaiian", price=1199, category_id=cat1.id, description="Ham and pineapple"),
            Product(name="Coca-Cola", price=199, category_id=cat2.id, description="330ml can"),
            Product(name="Water", price=99, category_id=cat2.id, description="500ml bottle"),
        ])

        r2 = Restaurant(name="Sushi Star", description="Fresh Japanese cuisine", is_active=True)
        session.add(r2)
        await session.flush()
        cat3 = Category(name="Rolls", restaurant_id=r2.id)
        cat4 = Category(name="Sashimi", restaurant_id=r2.id)
        session.add_all([cat3, cat4])
        await session.flush()
        session.add_all([
            Product(name="California Roll", price=1299, category_id=cat3.id, description="Crab, avocado, cucumber"),
            Product(name="Spicy Tuna Roll", price=1399, category_id=cat3.id, description="Fresh tuna with spicy sauce"),
            Product(name="Salmon Sashimi", price=1599, category_id=cat4.id, description="5 pieces of fresh salmon"),
            Product(name="Tuna Sashimi", price=1699, category_id=cat4.id, description="5 pieces of fresh tuna"),
        ])

        r3 = Restaurant(name="Burger Barn", description="Gourmet burgers and fries", is_active=True)
        session.add(r3)
        await session.flush()
        cat5 = Category(name="Burgers", restaurant_id=r3.id)
        cat6 = Category(name="Sides", restaurant_id=r3.id)
        session.add_all([cat5, cat6])
        await session.flush()
        session.add_all([
            Product(name="Classic Burger", price=999, category_id=cat5.id, description="Beef patty with lettuce and tomato"),
            Product(name="Cheese Burger", price=1099, category_id=cat5.id, description="With cheddar cheese"),
            Product(name="Bacon Burger", price=1299, category_id=cat5.id, description="Crispy bacon and BBQ sauce"),
            Product(name="French Fries", price=399, category_id=cat6.id, description="Crispy golden fries"),
            Product(name="Onion Rings", price=499, category_id=cat6.id, description="Beer-battered onion rings"),
        ])

        await session.commit()
        logger.info("Seeded 3 restaurants with 14 products.")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    engine = create_engine()
    await init_db(engine)
    session_factory = create_session_factory(engine)

    await seed_if_empty(session_factory)

    # Start WebApp HTTP server
    webapp_app = web.Application()
    webapp_routes = create_webapp_routes(session_factory, settings.bot_token)
    webapp_app.router.add_routes(webapp_routes)

    runner = web.AppRunner(webapp_app)
    await runner.setup()
    port = int(os.environ.get("PORT", settings.webapp_port))
    site = web.TCPSite(runner, settings.webapp_host, port)
    await site.start()
    logger.info("WebApp server started on %s:%s", settings.webapp_host, port)

    # Start Telegram bot polling
    if settings.bot_token and settings.bot_token != "your_telegram_bot_token":
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode

        from app.handlers import setup_routers
        from app.middlewares import DbSessionMiddleware

        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        from aiogram import Dispatcher

        dp = Dispatcher()
        dp.update.middleware(DbSessionMiddleware(session_factory))
        dp.include_router(setup_routers())

        logger.info("Starting Telegram bot polling...")
        try:
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
    else:
        logger.warning("BOT_BOT_TOKEN not set, running WebApp server only.")
        await asyncio.Event().wait()

    await runner.cleanup()
    await close_db(engine)


if __name__ == "__main__":
    asyncio.run(main())
