from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class FulfillmentType(str, Enum):
    delivery = "delivery"
    pickup   = "pickup"


class OrderStatus(str, Enum):
    pending   = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready     = "ready"
    delivered = "delivered"
    cancelled = "cancelled"


class Category(SQLModel, table=True):
    id:         Optional[int] = Field(default=None, primary_key=True)
    name:       str           = Field(index=True, unique=True)
    slug:       str           = Field(index=True, unique=True)
    sort_order: int           = Field(default=0)


class Product(SQLModel, table=True):
    id:           Optional[int] = Field(default=None, primary_key=True)
    name:         str           = Field(index=True)
    slug:         str           = Field(index=True, unique=True)
    description:  str
    price:        float
    image_url:    Optional[str] = None
    category_id:  int           = Field(foreign_key="category.id")
    is_available: bool          = Field(default=True)
    is_featured:  bool          = Field(default=False)
    is_vegetarian:bool          = Field(default=False)
    is_spicy:     bool          = Field(default=False)
    sort_order:   int           = Field(default=0)
    # Peso relativo di preparazione usato per il carico degli slot ordini.
    # 1.0 = una pizza. Bevande/extra pesano meno perché non impegnano il forno.
    prep_weight:  float         = Field(default=1.0)


class Order(SQLModel, table=True):
    id:               Optional[int]    = Field(default=None, primary_key=True)
    customer_name:    str
    phone:            str
    customer_email:   str
    address:          Optional[str]    = None
    fulfillment_type: FulfillmentType
    slot_label:       str              = Field(index=True)
    status:           OrderStatus      = Field(default=OrderStatus.pending, index=True)
    total_price:      float            = Field(default=0.0)
    created_at:       datetime         = Field(default_factory=lambda: datetime.now(timezone.utc))

    items: List["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    id:           Optional[int] = Field(default=None, primary_key=True)
    order_id:     int           = Field(foreign_key="order.id")
    product_id:   int           = Field(foreign_key="product.id")
    product_name: str
    quantity:     int
    unit_price:   float
    line_total:   float
    # Snapshot del prep_weight del prodotto al momento dell'ordine (come unit_price):
    # se il peso del prodotto cambia in futuro, gli ordini storici restano coerenti.
    prep_weight:  float         = Field(default=1.0)

    order: Optional[Order] = Relationship(back_populates="items")
