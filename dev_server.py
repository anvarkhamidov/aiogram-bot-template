"""Development server — starts WebApp with seeded sample data."""
import asyncio

from aiohttp import web

from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User
from app.webapp.routes import create_webapp_routes
from database.engine import create_engine, create_session_factory, init_db

DEMO_TOKEN = "demo"


async def seed_data(session_factory):
    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(select(Restaurant))
        if result.scalars().first():
            print("Data already seeded.")
            return

        # User for demo
        user = User(telegram_id=1, first_name="Demo User")
        session.add(user)

        # Restaurant 1 — Pizza
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

        # Restaurant 2 — Sushi
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

        # Restaurant 3 — Burgers
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
        print("Sample data seeded: 3 restaurants, 6 categories, 14 products")


async def main():
    engine = create_engine("sqlite+aiosqlite:///data/food_delivery.db")
    await init_db(engine)
    session_factory = create_session_factory(engine)

    await seed_data(session_factory)

    app = web.Application()
    routes = create_webapp_routes(session_factory, DEMO_TOKEN)
    app.router.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    print("\n" + "=" * 50)
    print("  Food Delivery WebApp is running!")
    print("  Open: http://localhost:8080/webapp")
    print("=" * 50 + "\n")

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
