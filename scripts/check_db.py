from sqlmodel import Session, select
from app.db import engine
from app.db_models import Category, Product

with Session(engine) as session:
    categories = session.exec(select(Category)).all()
    products = session.exec(select(Product)).all()

    print("Categorie:", len(categories))
    print("Prodotti:", len(products))

    for c in categories:
        print(c)

    for p in products[:5]:
        print(p)
