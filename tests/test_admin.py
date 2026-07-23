"""Test per il pannello di amministrazione (login, ordini, menu)."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db_models import Category, FulfillmentType, Order, OrderStatus, Product


def _login(client: TestClient):
    return client.post(
        "/admin/login",
        data={"username": "testadmin", "password": "pizza"},
        follow_redirects=False,
    )


def _seed_product(session: Session, price: float = 6.50, available: bool = True) -> Product:
    cat = Category(name="Pizze", slug="pizze", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    product = Product(
        name="Margherita", slug="margherita", description="Pomodoro e mozzarella",
        price=price, category_id=cat.id, is_available=available,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def _seed_order(session: Session, product: Product, status: str = "pending") -> Order:
    order = Order(
        customer_name="Mario Rossi", phone="3331234567", customer_email="mario@example.com",
        fulfillment_type=FulfillmentType.pickup, slot_label="18:15",
        status=status, total_price=product.price,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ── Autenticazione ───────────────────────────────────────────

def test_admin_redirects_to_login_when_unauthenticated(client: TestClient):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/admin/login" in response.headers["location"]


def test_login_success(client: TestClient):
    response = _login(client)
    assert response.status_code == 303
    assert "admin_session" in response.cookies


def test_login_wrong_password(client: TestClient):
    response = client.post("/admin/login", data={"username": "testadmin", "password": "wrong"})
    assert response.status_code == 401


def test_login_wrong_username(client: TestClient):
    response = client.post("/admin/login", data={"username": "nope", "password": "pizza"})
    assert response.status_code == 401


def test_logout_requires_new_login(client: TestClient):
    _login(client)
    client.post("/admin/logout", follow_redirects=False)
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (302, 303)


# ── Dashboard ordini ─────────────────────────────────────────

def test_dashboard_shows_todays_orders(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    _seed_order(session, product)
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Mario Rossi" in response.text


def test_dashboard_filters_by_status(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    _seed_order(session, product, status="pending")
    _seed_order(session, product, status="ready")
    response = client.get("/admin", params={"status": "ready"})
    assert response.status_code == 200


# ── Aggiornamento stato ordine ───────────────────────────────

def test_update_order_status_valid(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    order = _seed_order(session, product)
    response = client.post(
        f"/admin/order/{order.id}/status", data={"status": "ready"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "aggiornato" in response.text
    session.refresh(order)
    assert order.status == OrderStatus.ready


def test_update_order_status_invalid_value_rejected(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    order = _seed_order(session, product)
    response = client.post(
        f"/admin/order/{order.id}/status", data={"status": "stato_a_caso"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "non valido" in response.text
    session.refresh(order)
    assert order.status == OrderStatus.pending  # invariato


def test_update_order_status_nonexistent_order(client: TestClient):
    _login(client)
    response = client.post("/admin/order/9999/status", data={"status": "ready"}, follow_redirects=True)
    assert "non trovato" in response.text


# ── Ordine telefonico ────────────────────────────────────────

def _telefono_payload(product_id: int, quantity: int = 1, slot: str = "18:15", **overrides) -> dict:
    payload = {
        "customer_name": "Luigi Bianchi",
        "phone": "3339876543",
        "fulfillment_type": "pickup",
        "slot_label": slot,
        "status": "confirmed",
        "product_ids": [product_id],
        "quantities": [quantity],
    }
    payload.update(overrides)
    return payload


def test_telefono_order_success(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post("/admin/telefono", data=_telefono_payload(product.id), follow_redirects=True)
    assert "creato con successo" in response.text


def test_telefono_order_no_products(client: TestClient, session: Session):
    _login(client)
    response = client.post(
        "/admin/telefono",
        data={
            "customer_name": "Luigi Bianchi", "phone": "3339876543",
            "fulfillment_type": "pickup", "slot_label": "18:15", "status": "confirmed",
        },
        follow_redirects=True,
    )
    assert "Aggiungi almeno un prodotto" in response.text


def test_telefono_order_quantity_over_limit(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(
        "/admin/telefono", data=_telefono_payload(product.id, quantity=25), follow_redirects=True
    )
    assert "Quantità massima" in response.text


def test_telefono_order_unavailable_product_blocked(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session, available=False)
    response = client.post("/admin/telefono", data=_telefono_payload(product.id), follow_redirects=True)
    assert "non è al momento disponibile" in response.text


def test_telefono_order_invalid_fulfillment_type(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(
        "/admin/telefono",
        data=_telefono_payload(product.id, fulfillment_type="drone"),
        follow_redirects=True,
    )
    assert "Modalità di consegna non valida" in response.text


def test_telefono_order_custom_slot_valid_format_succeeds(client: TestClient, session: Session):
    """L'opzione 'Altro orario...' deve accettare un HH:MM valido non nella lista predefinita."""
    _login(client)
    product = _seed_product(session)
    response = client.post(
        "/admin/telefono", data=_telefono_payload(product.id, slot="23:45"), follow_redirects=True
    )
    assert "creato con successo" in response.text


def test_telefono_order_invalid_slot_format_rejected(client: TestClient, session: Session):
    """Se il valore '__custom__' arriva al backend senza un orario valido, va rifiutato."""
    _login(client)
    product = _seed_product(session)
    response = client.post(
        "/admin/telefono", data=_telefono_payload(product.id, slot="__custom__"), follow_redirects=True
    )
    assert "Orario non valido" in response.text


def test_telefono_order_invalid_status(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(
        "/admin/telefono", data=_telefono_payload(product.id, status="stato_a_caso"), follow_redirects=True
    )
    assert "Stato ordine non valido" in response.text


def test_telefono_order_respects_slot_capacity(client: TestClient, session: Session):
    """Stessa capacità pesata usata per gli ordini online (MAX_WEIGHT_PER_SLOT)."""
    from app.api.orders import MAX_WEIGHT_PER_SLOT
    _login(client)
    product = _seed_product(session)  # prep_weight di default = 1.0
    limit = int(MAX_WEIGHT_PER_SLOT["pickup"])

    for _ in range(limit):
        r = client.post("/admin/telefono", data=_telefono_payload(product.id, slot="19:00"), follow_redirects=True)
        assert "creato con successo" in r.text

    r = client.post("/admin/telefono", data=_telefono_payload(product.id, slot="19:00"), follow_redirects=True)
    assert "capacità sufficiente" in r.text


# ── Gestione menu ────────────────────────────────────────────

def test_add_product(client: TestClient, session: Session):
    _login(client)
    cat = Category(name="Bevande", slug="bevande", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    response = client.post(
        "/admin/menu/product/add",
        data={
            "name": "Acqua naturale", "description": "Bottiglia 50cl",
            "price": "1.50", "category_id": cat.id, "sort_order": "1",
        },
        follow_redirects=True,
    )
    assert "aggiunto correttamente" in response.text


def test_edit_product(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(
        f"/admin/menu/product/{product.id}/edit",
        data={
            "name": "Margherita Speciale", "description": "Nuova descrizione",
            "price": "7.00", "category_id": product.category_id, "sort_order": "1",
        },
        follow_redirects=True,
    )
    assert "modificato con successo" in response.text
    session.refresh(product)
    assert product.name == "Margherita Speciale"
    assert product.price == 7.00


def test_add_product_negative_price_rejected(client: TestClient, session: Session):
    _login(client)
    cat = Category(name="Pizze", slug="pizze", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    response = client.post(
        "/admin/menu/product/add",
        data={
            "name": "Prezzo negativo", "description": "x",
            "price": "-5.00", "category_id": cat.id, "sort_order": "0",
        },
    )
    assert response.status_code == 422
    assert "text/html" in response.headers["content-type"]  # non JSON grezzo


def test_edit_nonexistent_product(client: TestClient, session: Session):
    _login(client)
    cat = Category(name="Pizze", slug="pizze", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    response = client.post(
        "/admin/menu/product/9999/edit",
        data={"name": "X", "description": "X", "price": "1.0", "category_id": cat.id, "sort_order": "0"},
        follow_redirects=True,
    )
    assert "non trovato" in response.text


def test_delete_product(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(f"/admin/menu/product/{product.id}/delete", follow_redirects=True)
    assert "eliminato con successo" in response.text
    assert session.get(Product, product.id) is None


def test_toggle_availability_twice_no_crash(client: TestClient, session: Session):
    """Regressione: il toggle andava in DetachedInstanceError (500) prima del fix."""
    _login(client)
    product = _seed_product(session, available=True)

    r1 = client.post(f"/admin/menu/product/{product.id}/toggle", follow_redirects=True)
    assert r1.status_code == 200
    assert "non disponibile" in r1.text

    r2 = client.post(f"/admin/menu/product/{product.id}/toggle", follow_redirects=True)
    assert r2.status_code == 200
    assert "ora disponibile" in r2.text


def test_add_category(client: TestClient, session: Session):
    _login(client)
    response = client.post(
        "/admin/menu/category/add", data={"name": "Dolci", "sort_order": "5"}, follow_redirects=True
    )
    assert "aggiunta correttamente" in response.text


def test_delete_empty_category(client: TestClient, session: Session):
    _login(client)
    cat = Category(name="Dolci", slug="dolci", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)
    response = client.post(f"/admin/menu/category/{cat.id}/delete", follow_redirects=True)
    assert "eliminata con successo" in response.text


def test_delete_category_with_products_blocked(client: TestClient, session: Session):
    _login(client)
    product = _seed_product(session)
    response = client.post(f"/admin/menu/category/{product.category_id}/delete", follow_redirects=True)
    assert "Impossibile eliminare" in response.text


# ── Storico ──────────────────────────────────────────────────

def test_storico_invalid_date_falls_back(client: TestClient):
    _login(client)
    response = client.get("/admin/storico", params={"data": "non-una-data"})
    assert response.status_code == 200
    assert "non valida" in response.text
