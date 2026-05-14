from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, field_validator
import re

MAX_QUANTITY_PER_PRODUCT = 20


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=MAX_QUANTITY_PER_PRODUCT)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    phone: str
    address: str | None = Field(default=None, max_length=200)
    fulfillment_type: str  # "delivery" | "pickup"
    slot_label: str
    items: List[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-().+]", "", v)
        if not re.match(r"^\d{7,15}$", cleaned):
            raise ValueError("Numero di telefono non valido")
        return v

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[\w\s'\-\u00e0\u00e1\u00e8\u00e9\u00ec\u00ed\u00f2\u00f3\u00f9\u00fa]+$", v, re.UNICODE):
            raise ValueError("Nome non valido: caratteri non permessi")
        return v.strip()

    @field_validator("fulfillment_type")
    @classmethod
    def validate_fulfillment(cls, v: str) -> str:
        if v not in ("delivery", "pickup"):
            raise ValueError("fulfillment_type deve essere 'delivery' o 'pickup'")
        return v


class SlotCheckRequest(BaseModel):
    fulfillment_type: str
    slot_label: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SlotCheckResponse(BaseModel):
    available: bool
    requested_slot: str
    alternatives: List[str]


class OrderCreateResponse(BaseModel):
    success: bool
    order_id: int
    status: str
    total_price: float
    slot_label: str
