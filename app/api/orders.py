from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import func
from sqlmodel import Session, select

from app.config import MAX_QUANTITY_PER_PRODUCT
from app.db import get_session
from app.db_models import FulfillmentType, Order, OrderItem, Product
from app.email_service import send_order_receipt
from app.limiter import limiter
from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    OrderItemCreate,
    SlotCheckRequest,
    SlotCheckResponse,
)

router = APIRouter(prefix="/api", tags=["orders"])

DELIVERY_SLOTS = ["18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
PICKUP_SLOTS   = ["18:15", "18:45", "19:15", "19:45", "20:15", "20:45", "21:15"]

# Capacità espressa in "unità di peso" invece che in numero di ordini:
# una pizza pesa 1.0 (vedi Product.prep_weight), bevande ed extra pesano meno
# perché non impegnano il forno. Valori di partenza da tarare sul carico reale
# della cucina.
MAX_WEIGHT_PER_SLOT = {
    FulfillmentType.delivery: 6.0,
    FulfillmentType.pickup:   10.0,
}


def get_slots_by_type(fulfillment_type: FulfillmentType) -> List[str]:
    if fulfillment_type == FulfillmentType.delivery:
        return DELIVERY_SLOTS
    if fulfillment_type == FulfillmentType.pickup:
        return PICKUP_SLOTS
    return []


def _get_used_weight(session: Session, fulfillment_type: FulfillmentType, slot_label: str) -> float:
    """Somma il peso (quantità × prep_weight) degli ordini attivi su uno slot."""
    total = session.exec(
        select(func.sum(OrderItem.quantity * OrderItem.prep_weight))
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.fulfillment_type == fulfillment_type,
            Order.slot_label == slot_label,
            Order.status.in_(["pending", "confirmed"]),
        )
    ).one()
    return total or 0.0


def _compute_order_weight(session: Session, items: List[OrderItemCreate]) -> float:
    """Calcola il peso totale di un carrello sommando quantità × prep_weight
    del prodotto reale nel DB (mai fidarsi del peso calcolato lato client)."""
    merged: dict[int, int] = {}
    for item in items:
        merged[item.product_id] = merged.get(item.product_id, 0) + item.quantity

    weight = 0.0
    for product_id, quantity in merged.items():
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Prodotto con id {product_id} non trovato nel menu")
        weight += product.prep_weight * quantity
    return weight


def slot_is_available(
    session: Session,
    fulfillment_type: FulfillmentType,
    slot_label: str,
    extra_weight: float = 0.0,
) -> bool:
    """extra_weight è il peso del carrello che si vuole aggiungere allo slot:
    0.0 (default) indica solo 'lo slot ha ancora un minimo di spazio'."""
    limit = MAX_WEIGHT_PER_SLOT.get(fulfillment_type, 0.0)
    return _get_used_weight(session, fulfillment_type, slot_label) + extra_weight <= limit


def _claim_slot_or_raise(
    session: Session,
    fulfillment_type: FulfillmentType,
    slot_label: str,
    order_weight: float,
) -> None:
    """Verifica la disponibilità dello slot dentro la transazione corrente.
    Va chiamato il più tardi possibile prima di session.add(order)
    per minimizzare la finestra della race condition."""
    if not slot_is_available(session, fulfillment_type, slot_label, order_weight):
        raise HTTPException(status_code=409, detail="Lo slot selezionato non è più disponibile")


def get_alternative_slots(
    session: Session,
    fulfillment_type: FulfillmentType,
    exclude_slot: str,
    extra_weight: float = 0.0,
) -> List[str]:
    available = []
    for slot in get_slots_by_type(fulfillment_type):
        if slot == exclude_slot:
            continue
        if slot_is_available(session, fulfillment_type, slot, extra_weight):
            available.append(slot)
    return available[:3]


@router.get("/slots")
@limiter.limit("30/minute")
def get_slots(
    request: Request,
    fulfillment_type: str,
    session: Session = Depends(get_session),
):
    if fulfillment_type not in (FulfillmentType.delivery, FulfillmentType.pickup):
        raise HTTPException(status_code=400, detail="fulfillment_type non valido: usa 'delivery' o 'pickup'")

    ft = FulfillmentType(fulfillment_type)
    result = [
        {"label": slot, "available": slot_is_available(session, ft, slot)}
        for slot in get_slots_by_type(ft)
    ]
    return {"fulfillment_type": fulfillment_type, "slots": result}


@router.post("/orders/check-slot", response_model=SlotCheckResponse)
@limiter.limit("20/minute")
def check_slot(
    request: Request,
    payload: SlotCheckRequest,
    session: Session = Depends(get_session),
):
    valid_slots = get_slots_by_type(payload.fulfillment_type)
    if payload.slot_label not in valid_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Slot '{payload.slot_label}' non valido per {payload.fulfillment_type}"
        )

    order_weight = _compute_order_weight(session, payload.items)

    available   = slot_is_available(session, payload.fulfillment_type, payload.slot_label, order_weight)
    alternatives = [] if available else get_alternative_slots(
        session, payload.fulfillment_type, payload.slot_label, order_weight
    )
    return SlotCheckResponse(
        available=available,
        requested_slot=payload.slot_label,
        alternatives=alternatives,
    )


@router.post("/orders", response_model=OrderCreateResponse)
@limiter.limit("10/minute")
def create_order(
    request: Request,
    payload: OrderCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    if payload.fulfillment_type == FulfillmentType.delivery and not (payload.address or "").strip():
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

    total_price = 0.0
    order_weight = 0.0
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
        order_weight += product.prep_weight * quantity

        order_items_to_create.append({
            "product_id":   product.id,
            "product_name": product.name,
            "quantity":     quantity,
            "unit_price":   product.price,
            "line_total":   line_total,
            "prep_weight":  product.prep_weight,
        })

    # Il check slot viene fatto il più tardi possibile, dentro la stessa sessione,
    # subito prima dell'insert: minimizza la finestra della race condition.
    _claim_slot_or_raise(session, payload.fulfillment_type, payload.slot_label, order_weight)

    order = Order(
        customer_name    = payload.customer_name,
        phone            = payload.phone,
        customer_email   = payload.customer_email,
        address          = payload.address,
        fulfillment_type = payload.fulfillment_type,
        slot_label       = payload.slot_label,
        status           = "pending",
        total_price      = round(total_price, 2),
    )

    # Ordine e righe vanno salvati nella STESSA transazione: il controllo capacità
    # somma il peso delle righe (OrderItem), quindi un commit intermedio dopo il
    # solo Order rilascerebbe il lock BEGIN IMMEDIATE prima che le righe esistano,
    # e una richiesta concorrente vedrebbe lo slot ancora libero (overbooking).
    # flush() assegna order.id senza chiudere la transazione.
    session.add(order)
    session.flush()

    for item in order_items_to_create:
        session.add(OrderItem(
            order_id     = order.id,
            product_id   = item["product_id"],
            product_name = item["product_name"],
            quantity     = item["quantity"],
            unit_price   = item["unit_price"],
            line_total   = item["line_total"],
            prep_weight  = item["prep_weight"],
        ))

    session.commit()
    session.refresh(order)

    background_tasks.add_task(send_order_receipt, order, order_items_to_create)

    return OrderCreateResponse(
        success     = True,
        order_id    = order.id,
        status      = order.status,
        total_price = order.total_price,
        slot_label  = order.slot_label,
    )
