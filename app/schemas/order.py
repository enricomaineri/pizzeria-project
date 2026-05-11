import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)


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

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Il nome deve avere almeno 2 caratteri")
        if not re.fullmatch(r"[a-zA-Z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u00FF' ]+", v):
            raise ValueError("Il nome può contenere solo lettere, spazi e apostrofi")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        # Normalizza: rimuove spazi, trattini, punti e prefisso +39 / 0039
        n = re.sub(r"[\s\-\.]", "", v.strip())
        if n.startswith("+39"):
            n = n[3:]
        elif n.startswith("0039"):
            n = n[4:]
        if not re.fullmatch(r"\d+", n):
            raise ValueError("Il numero di telefono deve contenere solo cifre")
        if len(n) != 10:
            raise ValueError(f"Il numero di telefono deve avere 10 cifre (inserite: {len(n)})")
        if not re.match(r"^[03]", n):
            raise ValueError("Il numero deve iniziare con 0 (fisso) o 3 (cellulare)")
        return n  # salva sempre in formato normalizzato (10 cifre)

    @field_validator("address")
    @classmethod
    def validate_address(cls, v, info):
        # L'indirizzo è obbligatorio solo per la consegna a domicilio;
        # il controllo sul fulfillment_type avviene in orders.py,
        # qui validiamo solo il formato se il valore è presente.
        if v is None:
            return v
        v = v.strip()
        if len(v) < 8:
            raise ValueError("L'indirizzo è troppo corto. Indica via, nome via e numero civico")
        if not re.search(r"[a-zA-Z\u00C0-\u00FF]", v):
            raise ValueError("L'indirizzo deve contenere il nome della via")
        if not re.search(r"\d", v):
            raise ValueError("L'indirizzo deve includere il numero civico")
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
