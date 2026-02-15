from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_from_cart(
        self,
        user_id: int,
        restaurant_id: int,
        cart_items: list[CartItem],
        delivery_address: str,
        phone: str,
        comment: str | None = None,
    ) -> Order:
        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order(
            user_id=user_id,
            restaurant_id=restaurant_id,
            status=OrderStatus.PENDING,
            total=total,
            delivery_address=delivery_address,
            phone=phone,
            comment=comment,
        )
        self.session.add(order)
        await self.session.flush()

        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
            self.session.add(order_item)

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_orders(self, user_id: int) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_orders(self, user_id: int) -> list[Order]:
        active_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.DELIVERING,
        ]
        stmt = (
            select(Order)
            .where(Order.user_id == user_id, Order.status.in_(active_statuses))
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, order_id: int, status: OrderStatus) -> Order | None:
        order = await self.get_by_id(order_id)
        if order:
            order.status = status
            await self.session.commit()
            await self.session.refresh(order)
        return order

    async def cancel(self, order_id: int, user_id: int) -> Order | None:
        order = await self.get_by_id(order_id)
        if order and order.user_id == user_id and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            await self.session.commit()
            await self.session.refresh(order)
            return order
        return None

    async def get_all_pending(self) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.status == OrderStatus.PENDING)
            .order_by(Order.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
