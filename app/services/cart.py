from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartItem
from app.models.user import User


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_items(self, user_id: int) -> list[CartItem]:
        stmt = select(CartItem).where(CartItem.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_item(self, user_id: int, product_id: int, quantity: int = 1) -> CartItem:
        stmt = select(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            self.session.add(item)

        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update_quantity(self, item_id: int, quantity: int) -> CartItem | None:
        stmt = select(CartItem).where(CartItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if item is None:
            return None

        if quantity <= 0:
            await self.session.delete(item)
            await self.session.commit()
            return None

        item.quantity = quantity
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def remove_item(self, item_id: int) -> bool:
        stmt = select(CartItem).where(CartItem.id == item_id)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
            return True
        return False

    async def clear(self, user_id: int) -> None:
        stmt = delete(CartItem).where(CartItem.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_total(self, user_id: int) -> int:
        items = await self.get_items(user_id)
        return sum(item.subtotal for item in items)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
