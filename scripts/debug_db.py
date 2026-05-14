# Script di debug: stampa a console il contenuto attuale del database.
# Eseguire dalla root del progetto: python scripts/debug_db.py

from sqlmodel import Session, select
from app.db import engine
from app.db_models import Category, Product

with Session(engine) as session:
    categories = session.exec(select(Category)).all()
    products = session.exec(select(Product)).all()

    print(f"Categorie: {len(categories)}")
    for c in categories:
        print(f"  [{c.id}] {c.name} (slug: {c.slug})")

    print(f"\nProdotti: {len(products)}")
    for p in products[:10]:
        print(f"  [{p.id}] {p.name} — €{p.price:.2f} (disponibile: {p.is_available})")
