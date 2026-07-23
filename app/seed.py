from sqlmodel import Session, select
from app.db import engine
from app.db_models import Category, Product


def seed_data():
    with Session(engine) as session:
        existing = session.exec(select(Category)).first()
        if existing:
            return

        categories = [
            Category(name="Pizze classiche", slug="pizze-classiche", sort_order=1),
            Category(name="Pizze speciali", slug="pizze-speciali", sort_order=2),
            Category(name="Bevande", slug="bevande", sort_order=3),
            Category(name="Extra", slug="extra", sort_order=4),
        ]
        session.add_all(categories)
        session.commit()

        cat_map = {
            c.slug: c.id for c in session.exec(select(Category)).all()
        }

        products = [
            Product(
                name="Margherita",
                slug="margherita",
                description="Pomodoro, fiordilatte, basilico fresco.",
                price=6.50,
                category_id=cat_map["pizze-classiche"],
                is_available=True,
                is_vegetarian=True,
                sort_order=1,
            ),
            Product(
                name="Marinara",
                slug="marinara",
                description="Pomodoro, aglio, origano, olio EVO.",
                price=5.50,
                category_id=cat_map["pizze-classiche"],
                is_available=True,
                is_vegetarian=True,
                sort_order=2,
            ),
            Product(
                name="Diavola",
                slug="diavola",
                description="Pomodoro, fiordilatte, salame piccante.",
                price=8.50,
                category_id=cat_map["pizze-classiche"],
                is_available=True,
                is_featured=True,
                is_spicy=True,
                sort_order=3,
            ),
            Product(
                name="Capricciosa",
                slug="capricciosa",
                description="Pomodoro, fiordilatte, prosciutto, funghi, carciofi, olive.",
                price=9.00,
                category_id=cat_map["pizze-classiche"],
                is_available=True,
                sort_order=4,
            ),
            Product(
                name="Bufalina",
                slug="bufalina",
                description="Pomodoro, mozzarella di bufala, basilico fresco.",
                price=9.50,
                category_id=cat_map["pizze-speciali"],
                is_available=True,
                is_featured=True,
                sort_order=1,
            ),
            Product(
                name="Tartufo",
                slug="tartufo",
                description="Fiordilatte, crema tartufata, funghi, scaglie di grana.",
                price=11.50,
                category_id=cat_map["pizze-speciali"],
                is_available=True,
                sort_order=2,
            ),
            Product(
                name="Mortadella e Pistacchio",
                slug="mortadella-pistacchio",
                description="Fiordilatte, mortadella, granella di pistacchio, burrata.",
                price=11.00,
                category_id=cat_map["pizze-speciali"],
                is_available=True,
                sort_order=3,
            ),
            Product(
                name="Vegetale Deluxe",
                slug="vegetale-deluxe",
                description="Fiordilatte, zucchine, melanzane, peperoni, pomodorini.",
                price=9.50,
                category_id=cat_map["pizze-speciali"],
                is_available=True,
                is_vegetarian=True,
                sort_order=4,
            ),
            Product(
                name="Coca-Cola 33cl",
                slug="coca-cola-33",
                description="Lattina 33cl.",
                price=2.50,
                category_id=cat_map["bevande"],
                is_available=True,
                sort_order=1,
                prep_weight=0.2,
            ),
            Product(
                name="Coca-Cola Zero 33cl",
                slug="coca-cola-zero-33",
                description="Lattina 33cl.",
                price=2.50,
                category_id=cat_map["bevande"],
                is_available=True,
                sort_order=2,
                prep_weight=0.2,
            ),
            Product(
                name="Acqua naturale",
                slug="acqua-naturale",
                description="Bottiglia 50cl.",
                price=1.50,
                category_id=cat_map["bevande"],
                is_available=True,
                sort_order=3,
                prep_weight=0.2,
            ),
            Product(
                name="Birra 33cl",
                slug="birra-33",
                description="Bottiglia 33cl.",
                price=3.50,
                category_id=cat_map["bevande"],
                is_available=True,
                sort_order=4,
                prep_weight=0.2,
            ),
            Product(
                name="Bufala",
                slug="extra-bufala",
                description="Aggiunta di mozzarella di bufala.",
                price=2.00,
                category_id=cat_map["extra"],
                is_available=True,
                sort_order=1,
                prep_weight=0.4,
            ),
            Product(
                name="Burrata",
                slug="extra-burrata",
                description="Aggiunta di burrata.",
                price=2.50,
                category_id=cat_map["extra"],
                is_available=True,
                sort_order=2,
                prep_weight=0.4,
            ),
            Product(
                name="Salame piccante",
                slug="extra-salame-piccante",
                description="Aggiunta extra di salame piccante.",
                price=1.50,
                category_id=cat_map["extra"],
                is_available=True,
                sort_order=3,
                prep_weight=0.4,
            ),
        ]

        session.add_all(products)
        session.commit()