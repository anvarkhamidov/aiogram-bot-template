from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.restaurant import Restaurant


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"))

    restaurant: Mapped["Restaurant"] = relationship(back_populates="categories")
    products: Mapped[list["Product"]] = relationship(back_populates="category", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"
