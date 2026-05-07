from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    slug: str = Field(index=True, unique=True)
    sort_order: int = Field(default=0)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    description: str
    price: float
    image_url: Optional[str] = None
    category_id: int = Field(foreign_key="category.id")
    is_available: bool = Field(default=True)
    is_featured: bool = Field(default=False)
    is_vegetarian: bool = Field(default=False)
    is_spicy: bool = Field(default=False)
    sort_order: int = Field(default=0)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    phone: str
    address: Optional[str] = None
    fulfillment_type: str
    slot_label: str
    status: str = Field(default="pending")
    total_price: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    items: List["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

    order: Optional[Order] = Relationship(back_populates="items")