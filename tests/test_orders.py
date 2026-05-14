"""Test per la creazione ordini e la gestione degli slot."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db_models import Category, Product


# ── Fixture helpers ──────────────────────────────────────────────────────────

def _seed_product(session: Session, price: float = 8.0) -> Product:
    cat = Category(name="Pizze", slug="pizze", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    product = Product(
        name="Margherita",
        slug="margherita",
        description="Pomodoro e mozzarella",
        price=price,
        category_id=cat.id,
        is_available=True,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def _order_payload(product_id: int, slot: str = "18:30", fulfillment: str = "delivery") -> dict:
    return {
        "customer_name": "Mario Rossi",
        "phone": "3331234567",
        "address": "Via Roma 1",
        "fulfillment_type": fulfillment,
        "slot_label": slot,
        "items": [{"product_id": product_id, "quantity": 1}],
    }


# ── Test creazione ordine ────────────────────────────────────────────────────

def test_create_order_success(client: TestClient, session: Session):
    product = _seed_product(session)
    response = client.post("/api/orders", json=_order_payload(product.id))
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "pending"
    assert data["total_price"] == product.price


def test_create_order_product_not_found(client: TestClient, session: Session):
    response = client.post("/api/orders", json=_order_payload(product_id=9999))
    assert response.status_code == 404


def test_create_order_product_unavailable(client: TestClient, session: Session):
    product = _seed_product(session)
    product.is_available = False
    session.add(product)
    session.commit()

    response = client.post("/api/orders", json=_order_payload(product.id))
    assert response.status_code == 400
    assert "disponibile" in response.json()["detail"]


def test_create_order_invalid_slot(client: TestClient, session: Session):
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["slot_label"] = "99:99"
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 400


def test_create_order_delivery_requires_address(client: TestClient, session: Session):
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["address"] = ""
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 400
    assert "Indirizzo" in response.json()["detail"]


def test_create_order_pickup_no_address(client: TestClient, session: Session):
    """Pickup non richiede indirizzo."""
    product = _seed_product(session)
    payload = _order_payload(product.id, slot="18:15", fulfillment="pickup")
    payload.pop("address", None)
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 200


def test_create_order_invalid_fulfillment_type(client: TestClient, session: Session):
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["fulfillment_type"] = "drone"
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422


# ── Test slot ────────────────────────────────────────────────────────────────

def test_slot_becomes_unavailable_when_full(client: TestClient, session: Session):
    """Dopo MAX_ORDERS_PER_SLOT ordini lo slot deve risultare pieno (409)."""
    from app.api.orders import MAX_ORDERS_PER_SLOT
    product = _seed_product(session)
    limit = MAX_ORDERS_PER_SLOT["delivery"]

    for _ in range(limit):
        r = client.post("/api/orders", json=_order_payload(product.id, slot="18:30"))
        assert r.status_code == 200

    r = client.post("/api/orders", json=_order_payload(product.id, slot="18:30"))
    assert r.status_code == 409


def test_get_slots_delivery(client: TestClient):
    response = client.get("/api/slots", params={"fulfillment_type": "delivery"})
    assert response.status_code == 200
    data = response.json()
    assert data["fulfillment_type"] == "delivery"
    assert len(data["slots"]) > 0
    assert all("label" in s and "available" in s for s in data["slots"])


def test_get_slots_invalid_type(client: TestClient):
    response = client.get("/api/slots", params={"fulfillment_type": "bicicletta"})
    assert response.status_code == 400


# ── Test validazione input ───────────────────────────────────────────────────

def test_order_invalid_phone(client: TestClient, session: Session):
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["phone"] = "abc"
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422


def test_order_empty_items(client: TestClient, session: Session):
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["items"] = []
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422


def test_order_deduplicates_same_product(client: TestClient, session: Session):
    """Due righe con stesso product_id vengono sommate correttamente."""
    product = _seed_product(session)
    payload = _order_payload(product.id)
    payload["items"] = [
        {"product_id": product.id, "quantity": 1},
        {"product_id": product.id, "quantity": 2},
    ]
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 200
    assert response.json()["total_price"] == round(product.price * 3, 2)
