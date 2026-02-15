import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING
    )
    total: Mapped[int] = mapped_column(Integer)  # total in cents
    delivery_address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", lazy="selectin")

    @property
    def total_display(self) -> str:
        return f"{self.total / 100:.2f}"

    @property
    def status_emoji(self) -> str:
        emojis = {
            OrderStatus.PENDING: "",
            OrderStatus.CONFIRMED: "",
            OrderStatus.PREPARING: "",
            OrderStatus.DELIVERING: "",
            OrderStatus.DELIVERED: "",
            OrderStatus.CANCELLED: "",
        }
        return emojis.get(self.status, "")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status={self.status}, total={self.total})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)  # price at time of order

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(lazy="selectin")

    @property
    def subtotal(self) -> int:
        return self.price * self.quantity

    def __repr__(self) -> str:
        return f"<OrderItem(order={self.order_id}, product={self.product_id}, qty={self.quantity})>"
