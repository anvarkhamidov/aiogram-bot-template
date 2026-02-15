from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant


class RestaurantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> list[Restaurant]:
        stmt = select(Restaurant).where(Restaurant.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, restaurant_id: int) -> Restaurant | None:
        stmt = (
            select(Restaurant)
            .where(Restaurant.id == restaurant_id)
            .options(selectinload(Restaurant.categories).selectinload(Category.products))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_menu(self, restaurant_id: int) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.restaurant_id == restaurant_id)
            .options(selectinload(Category.products))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_product(self, product_id: int) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_restaurant(
        self, name: str, description: str | None = None, address: str | None = None
    ) -> Restaurant:
        restaurant = Restaurant(name=name, description=description, address=address)
        self.session.add(restaurant)
        await self.session.commit()
        await self.session.refresh(restaurant)
        return restaurant

    async def create_category(self, name: str, restaurant_id: int) -> Category:
        category = Category(name=name, restaurant_id=restaurant_id)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def create_product(
        self,
        name: str,
        price: int,
        category_id: int,
        description: str | None = None,
        image_url: str | None = None,
    ) -> Product:
        product = Product(
            name=name,
            price=price,
            category_id=category_id,
            description=description,
            image_url=image_url,
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product
