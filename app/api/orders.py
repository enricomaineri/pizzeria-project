from collections import Counter
from datetime import timezone
from typing import List

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import Session, select

from app.db import engine
from app.db_models import Order, OrderItem, Product
from app.limiter import limiter
from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    SlotCheckRequest,
    SlotCheckResponse,
)

router = APIRouter(prefix="/api", tags=["orders"])

DELIVERY_SLOTS = ["18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
PICKUP_SLOTS = ["18:15", "18:45", "19:15", "19:45", "20:15", "20:45", "21:15"]

MAX_ORDERS_PER_SLOT = {
    "delivery": 3,
    "pickup": 5,
}

MAX_QUANTITY_PER_PRODUCT = 20


def get_slots_by_type(fulfillment_type: str) -> List[str]:
    if fulfillment_type == "delivery":
        return DELIVERY_SLOTS
    if fulfillment_type == "pickup":
        return PICKUP_SLOTS
    return []


def slot_is_available(session: Session, fulfillment_type: str, slot_label: str) -> bool:
    statement = select(Order).where(
        Order.fulfillment_type == fulfillment_type,
        Order.slot_label == slot_label,
        Order.status.in_(["pending", "confirmed"])
    )
    orders = session.exec(statement).all()
    current_count = len(orders)
    limit = MAX_ORDERS_PER_SLOT.get(fulfillment_type, 0)
    return current_count < limit


def get_alternative_slots(session: Session, fulfillment_type: str, exclude_slot: str) -> List[str]:
    slots = get_slots_by_type(fulfillment_type)
    available = []
    for slot in slots:
        if slot == exclude_slot:
            continue
        if slot_is_available(session, fulfillment_type, slot):
            available.append(slot)
    return available[:3]


@router.get("/slots")
@limiter.limit("30/minute")
def get_slots(request: Request, fulfillment_type: str):
    if fulfillment_type not in ("delivery", "pickup"):
        raise HTTPException(status_code=400, detail="fulfillment_type non valido: usa 'delivery' o 'pickup'")

    with Session(engine) as session:
        result = []
        for slot in get_slots_by_type(fulfillment_type):
            result.append({
                "label": slot,
                "available": slot_is_available(session, fulfillment_type, slot)
            })
        return {"fulfillment_type": fulfillment_type, "slots": result}


@router.post("/orders/check-slot", response_model=SlotCheckResponse)
@limiter.limit("20/minute")
def check_slot(request: Request, payload: SlotCheckRequest):
    valid_slots = get_slots_by_type(payload.fulfillment_type)
    if payload.slot_label not in valid_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Slot '{payload.slot_label}' non valido per {payload.fulfillment_type}"
        )

    with Session(engine) as session:
        available = slot_is_available(session, payload.fulfillment_type, payload.slot_label)
        alternatives = [] if available else get_alternative_slots(
            session, payload.fulfillment_type, payload.slot_label
        )

    return SlotCheckResponse(
        available=available,
        requested_slot=payload.slot_label,
        alternatives=alternatives
    )


@router.post("/orders", response_model=OrderCreateResponse)
@limiter.limit("10/minute")
def create_order(request: Request, payload: OrderCreate):
    if payload.fulfillment_type == "delivery" and not (payload.address or "").strip():
        raise HTTPException(status_code=400, detail="Indirizzo obbligatorio per la consegna a domicilio")

    valid_slots = get_slots_by_type(payload.fulfillment_type)
    if payload.slot_label not in valid_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Slot '{payload.slot_label}' non valido per {payload.fulfillment_type}"
        )

    # Deduplicazione: somma quantità se stesso product_id appare più volte.
    merged: dict[int, int] = {}
    for item in payload.items:
        merged[item.product_id] = merged.get(item.product_id, 0) + item.quantity

    # Controllo quantità post-merge
    for product_id, quantity in merged.items():
        if quantity > MAX_QUANTITY_PER_PRODUCT:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Quantità massima per prodotto: {MAX_QUANTITY_PER_PRODUCT} "
                    f"(richiesto {quantity} per product_id={product_id})"
                )
            )

    with Session(engine) as session:
        if not slot_is_available(session, payload.fulfillment_type, payload.slot_label):
            raise HTTPException(status_code=409, detail="Lo slot selezionato non è più disponibile")

        total_price = 0.0
        order_items_to_create = []

        for product_id, quantity in merged.items():
            product = session.get(Product, product_id)

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Prodotto con id {product_id} non trovato nel menu"
                )

            if not product.is_available:
                raise HTTPException(
                    status_code=400,
                    detail=f"'{product.name}' non è al momento disponibile"
                )

            line_total = product.price * quantity
            total_price += line_total

            order_items_to_create.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": product.price,
                "line_total": line_total,
            })

        order = Order(
            customer_name=payload.customer_name,
            phone=payload.phone,
            address=payload.address,
            fulfillment_type=payload.fulfillment_type,
            slot_label=payload.slot_label,
            status="pending",
            total_price=round(total_price, 2),
        )

        session.add(order)
        session.commit()
        session.refresh(order)

        for item in order_items_to_create:
            session.add(OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                line_total=item["line_total"],
            ))

        session.commit()

        return OrderCreateResponse(
            success=True,
            order_id=order.id,
            status=order.status,
            total_price=order.total_price,
            slot_label=order.slot_label,
        )
