from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=50)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=5, max_length=30)
    address: Optional[str] = Field(default=None, max_length=300)
    fulfillment_type: str
    slot_label: str = Field(min_length=1, max_length=20)
    items: List[OrderItemCreate] = Field(min_length=1, max_length=30)

    @field_validator("customer_name", "phone", "slot_label", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("fulfillment_type")
    @classmethod
    def validate_fulfillment_type(cls, v):
        if v not in ("delivery", "pickup"):
            raise ValueError("fulfillment_type deve essere 'delivery' o 'pickup'")
        return v


class SlotCheckRequest(BaseModel):
    fulfillment_type: str
    slot_label: str = Field(min_length=1, max_length=20)

    @field_validator("fulfillment_type")
    @classmethod
    def validate_fulfillment_type(cls, v):
        if v not in ("delivery", "pickup"):
            raise ValueError("fulfillment_type deve essere 'delivery' o 'pickup'")
        return v


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
