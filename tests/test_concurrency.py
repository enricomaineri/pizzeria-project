"""Test di concorrenza reale sulla capacità degli slot ordini.

A differenza degli altri test (che condividono un'unica sessione in-memory),
qui serve un vero file SQLite e una sessione *nuova* per ogni richiesta,
altrimenti non si riproduce la race condition che vogliamo verificare essere
risolta (vedi il BEGIN IMMEDIATE in app/db.py).
"""
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.db_models import Category, Product


@pytest.fixture
def concurrent_client():
    """TestClient su un file SQLite reale con lo stesso locking della produzione
    (BEGIN IMMEDIATE), e una sessione nuova per ogni richiesta come in produzione."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _disable_pysqlite_begin(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(conn):
        conn.exec_driver_sql("BEGIN IMMEDIATE")

    SQLModel.metadata.create_all(engine)

    with Session(engine) as setup_session:
        cat = Category(name="Pizze", slug="pizze", sort_order=1)
        setup_session.add(cat)
        setup_session.commit()
        setup_session.refresh(cat)
        product = Product(
            name="Margherita", slug="margherita", description="Classica",
            price=6.50, category_id=cat.id, is_available=True, prep_weight=1.0,
        )
        setup_session.add(product)
        setup_session.commit()
        setup_session.refresh(product)
        product_id = product.id

    from app.main import app

    def fresh_session_override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = fresh_session_override
    client = TestClient(app, raise_server_exceptions=True)
    yield client, product_id
    app.dependency_overrides.clear()
    engine.dispose()  # rilascia le connessioni pool prima di cancellare il file (Windows)
    os.remove(path)


def _order_payload(product_id: int, slot: str, quantity: int = 1) -> dict:
    return {
        "customer_name": "Test Concorrenza",
        "phone": "3331234567",
        "customer_email": "test@example.com",
        "fulfillment_type": "pickup",
        "slot_label": slot,
        "items": [{"product_id": product_id, "quantity": quantity}],
    }


def test_concurrent_orders_never_exceed_slot_capacity(concurrent_client):
    """Regressione: senza BEGIN IMMEDIATE, richieste concorrenti passavano tutte
    il controllo di capacità prima che una qualunque commitasse, causando
    overbooking (verificato manualmente: 9.0 accettati su una capacità di 6.0)."""
    client, product_id = concurrent_client
    from app.api.orders import MAX_WEIGHT_PER_SLOT

    capacity = MAX_WEIGHT_PER_SLOT["pickup"]  # 10.0, peso per ordine = 1.0
    num_requests = int(capacity) + 6  # più richieste della capacità disponibile

    def make_order(_):
        return client.post("/api/orders", json=_order_payload(product_id, "18:15"))

    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        responses = list(executor.map(make_order, range(num_requests)))

    statuses = [r.status_code for r in responses]
    successes = statuses.count(200)
    conflicts = statuses.count(409)

    assert successes == int(capacity), f"Attesi {int(capacity)} successi, ottenuti {successes} (status: {statuses})"
    assert successes + conflicts == num_requests, "Nessuna risposta inattesa (solo 200 o 409 ammessi)"
