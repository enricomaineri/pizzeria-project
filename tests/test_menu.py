"""Test per le API del menu."""
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db_models import Category, Product


def _seed_menu(session: Session):
    cat = Category(name="Pizze", slug="pizze", sort_order=1)
    session.add(cat)
    session.commit()
    session.refresh(cat)

    products = [
        Product(name="Margherita", slug="margherita", description="Classica",
                price=6.50, category_id=cat.id, is_available=True, is_vegetarian=True),
        Product(name="Diavola", slug="diavola", description="Piccante",
                price=8.50, category_id=cat.id, is_available=True, is_spicy=True),
        Product(name="Stagionale", slug="stagionale", description="Non disponibile",
                price=9.00, category_id=cat.id, is_available=False),
    ]
    session.add_all(products)
    session.commit()
    return cat


def test_get_menu_returns_categories(client: TestClient, session: Session):
    _seed_menu(session)
    response = client.get("/api/menu")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Pizze"


def test_get_menu_excludes_unavailable(client: TestClient, session: Session):
    """I prodotti non disponibili non devono comparire nel menu pubblico."""
    _seed_menu(session)
    response = client.get("/api/menu")
    items = response.json()["categories"][0]["items"]
    names = [i["name"] for i in items]
    assert "Stagionale" not in names
    assert "Margherita" in names


def test_get_menu_empty(client: TestClient):
    """Menu senza prodotti: risposta valida con lista vuota."""
    response = client.get("/api/menu")
    assert response.status_code == 200
    assert response.json()["categories"] == []


def test_menu_item_fields(client: TestClient, session: Session):
    """Ogni item deve esporre i campi attesi."""
    _seed_menu(session)
    items = client.get("/api/menu").json()["categories"][0]["items"]
    for item in items:
        for field in ("id", "name", "slug", "description", "price",
                      "is_featured", "is_vegetarian", "is_spicy"):
            assert field in item, f"Campo mancante: {field}"
