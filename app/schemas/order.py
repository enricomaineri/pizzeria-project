# kept — contains active Pydantic schemas for order validation
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field, field_validator
import re

MAX_QUANTITY_PER_PRODUCT = 20


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=MAX_QUANTITY_PER_PRODUCT)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_phone: str
    customer_address: str = Field(..., min_length=5, max_length=200)
    notes: str | None = Field(default=None, max_length=500)
    slot_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-().+]", "", v)
        if not re.match(r"^\d{7,15}$", cleaned):
            raise ValueError("Numero di telefono non valido")
        return v

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[\w\s'\-àáèéìíòóùú]+$", v, re.UNICODE):
            raise ValueError("Nome non valido: caratteri non permessi")
        return v.strip()

    @field_validator("customer_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not re.match(r"^[\w\s',\.\-/àáèéìíòóùú]+$", v, re.UNICODE):
            raise ValueError("Indirizzo non valido: caratteri non permessi")
        return v.strip()


class OrderItemRead(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderRead(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    customer_address: str
    notes: str | None
    slot_id: int
    status: str
    total_price: float
    items: List[OrderItemRead]

    class Config:
        from_attributes = True
