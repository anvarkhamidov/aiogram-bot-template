import asyncio
import logging

from aiohttp import web

from app.bot import create_bot, create_dispatcher
from app.config import settings
from app.handlers import setup_routers
from app.middlewares import DbSessionMiddleware
from app.webapp.routes import create_webapp_routes
from database.engine import close_db, create_engine, create_session_factory, init_db

logger = logging.getLogger(__name__)


async def on_startup(app: web.Application) -> None:
    engine = create_engine()
    await init_db(engine)
    app["db_engine"] = engine
    app["session_factory"] = create_session_factory(engine)
    logger.info("Database initialized")


async def on_shutdown(app: web.Application) -> None:
    engine = app.get("db_engine")
    if engine:
        await close_db(engine)
    logger.info("Database connection closed")


def create_webapp_app() -> web.Application:
    """Create aiohttp app for serving WebApp API and static files."""
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = create_bot()
    dp = create_dispatcher()

    engine = create_engine()
    await init_db(engine)
    session_factory = create_session_factory(engine)

    dp.update.middleware(DbSessionMiddleware(session_factory))

    router = setup_routers()
    dp.include_router(router)

    # Setup aiohttp for WebApp
    webapp_app = web.Application()
    webapp_routes = create_webapp_routes(session_factory, settings.bot_token)
    webapp_app.router.add_routes(webapp_routes)

    runner = web.AppRunner(webapp_app)
    await runner.setup()
    site = web.TCPSite(runner, settings.webapp_host, settings.webapp_port)
    await site.start()
    logger.info("WebApp server started on %s:%s", settings.webapp_host, settings.webapp_port)

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await close_db(engine)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
