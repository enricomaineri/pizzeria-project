from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    address: Optional[str] = None
    fulfillment_type: str
    slot_label: str
    items: List[OrderItemCreate]


class SlotCheckRequest(BaseModel):
    fulfillment_type: str
    slot_label: str


class SlotCheckResponse(BaseModel):
    available: bool
    requested_slot: str
    alternatives: List[str] = []


class OrderCreateResponse(BaseModel):
    success: bool
    order_id: int
    status: str
    total_price: float
    slot_label: str