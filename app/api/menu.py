from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.db import get_session
from app.db_models import Category, Product
from app.templates_config import templates

router = APIRouter()


@router.get("/menu", response_class=HTMLResponse)
def menu_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"title": "Menu | Vesuvio"}
    )


@router.get("/api/menu")
def get_menu(session: Session = Depends(get_session)):
    categories = session.exec(
        select(Category).order_by(Category.sort_order)
    ).all()

    result = []

    for category in categories:
        products = session.exec(
            select(Product)
            .where(Product.category_id == category.id)
            .where(Product.is_available == True)
            .order_by(Product.sort_order)
        ).all()

        result.append({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "items": [
                {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "description": product.description,
                    "price": product.price,
                    "image_url": product.image_url,
                    "is_featured": product.is_featured,
                    "is_vegetarian": product.is_vegetarian,
                    "is_spicy": product.is_spicy,
                }
                for product in products
            ]
        })

    return {"categories": result}
