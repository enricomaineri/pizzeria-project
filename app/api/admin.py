from datetime import datetime, timedelta, date
from slugify import slugify

from fastapi import APIRouter, Request, Form, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional

from app.db import engine
from app.db_models import Order, OrderItem, Product, Category
from app.auth import require_admin

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


# ─────────────────────────────────────────────
# DASHBOARD ORDINI (solo oggi)
# ─────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    status: str | None = None,
    _admin: str = Depends(require_admin),
):
    now = datetime.now()
    start_of_day      = datetime(now.year, now.month, now.day)
    start_of_next_day = start_of_day + timedelta(days=1)

    with Session(engine) as session:
        today_orders = session.exec(
            select(Order).where(
                Order.created_at >= start_of_day,
                Order.created_at < start_of_next_day
            )
        ).all()

        pending_count   = len([o for o in today_orders if o.status == "pending"])
        confirmed_count = len([o for o in today_orders if o.status == "confirmed"])
        preparing_count = len([o for o in today_orders if o.status == "preparing"])
        ready_count     = len([o for o in today_orders if o.status == "ready"])
        delivered_count = len([o for o in today_orders if o.status == "delivered"])

        if status:
            filtered = [o for o in today_orders if o.status == status]
        else:
            filtered = sorted(today_orders, key=lambda o: o.created_at, reverse=True)

        orders_with_items = []
        for order in filtered:
            items = session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            ).all()
            orders_with_items.append({"order": order, "items": items})

    return templates.TemplateResponse(request, "admin.html", {
        "active_tab":        "orders",
        "orders_with_items": orders_with_items,
        "selected_status":   status,
        "pending_count":     pending_count,
        "confirmed_count":   confirmed_count,
        "preparing_count":   preparing_count,
        "ready_count":       ready_count,
        "delivered_count":   delivered_count,
        "today_label":       now.strftime("%A %d %B %Y"),
    })


@router.post("/admin/order/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str = Form(...),
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Ordine non trovato")
        order.status = status
        session.add(order)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)


# ─────────────────────────────────────────────
# STORICO ORDINI (per data)
# ─────────────────────────────────────────────

@router.get("/admin/storico", response_class=HTMLResponse)
def admin_storico(
    request: Request,
    data: str | None = Query(default=None),
    status: str | None = None,
    _admin: str = Depends(require_admin),
):
    if data:
        try:
            selected_date = date.fromisoformat(data)
        except ValueError:
            selected_date = date.today() - timedelta(days=1)
    else:
        selected_date = date.today() - timedelta(days=1)

    start = datetime(selected_date.year, selected_date.month, selected_date.day)
    end   = start + timedelta(days=1)

    with Session(engine) as session:
        statement = select(Order).where(
            Order.created_at >= start,
            Order.created_at < end
        ).order_by(Order.created_at.desc())

        if status:
            statement = select(Order).where(
                Order.created_at >= start,
                Order.created_at < end,
                Order.status == status
            ).order_by(Order.created_at.desc())

        orders = session.exec(statement).all()

        orders_with_items = []
        for order in orders:
            items = session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            ).all()
            orders_with_items.append({"order": order, "items": items})

        total_day = sum(o.total_price for o in orders)

    return templates.TemplateResponse(request, "admin.html", {
        "active_tab":          "storico",
        "orders_with_items":   orders_with_items,
        "selected_status":     status,
        "selected_date":       selected_date.isoformat(),
        "selected_date_label": selected_date.strftime("%A %d %B %Y"),
        "total_day":           total_day,
        "order_count":         len(orders),
    })


# ─────────────────────────────────────────────
# GESTIONE MENU
# ─────────────────────────────────────────────

@router.get("/admin/menu", response_class=HTMLResponse)
def admin_menu(
    request: Request,
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        categories = session.exec(select(Category).order_by(Category.sort_order)).all()
        products   = session.exec(select(Product).order_by(Product.category_id, Product.sort_order)).all()

    return templates.TemplateResponse(request, "admin.html", {
        "active_tab": "menu",
        "categories": categories,
        "products":   products,
    })


@router.post("/admin/menu/product/add")
def add_product(
    name:          str   = Form(...),
    description:   str   = Form(...),
    price:         float = Form(...),
    category_id:   int   = Form(...),
    image_url:     str   = Form(""),
    is_available:  Optional[str] = Form(None),
    is_featured:   Optional[str] = Form(None),
    is_vegetarian: Optional[str] = Form(None),
    is_spicy:      Optional[str] = Form(None),
    sort_order:    int   = Form(0),
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        product = Product(
            name          = name,
            slug          = slugify(name),
            description   = description,
            price         = price,
            category_id   = category_id,
            image_url     = image_url or None,
            is_available  = is_available  == "on",
            is_featured   = is_featured   == "on",
            is_vegetarian = is_vegetarian == "on",
            is_spicy      = is_spicy      == "on",
            sort_order    = sort_order,
        )
        session.add(product)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)


@router.get("/admin/menu/product/{product_id}/edit", response_class=HTMLResponse)
def edit_product_form(
    request: Request,
    product_id: int,
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        product    = session.get(Product, product_id)
        categories = session.exec(select(Category).order_by(Category.sort_order)).all()
        products   = session.exec(select(Product).order_by(Product.category_id, Product.sort_order)).all()
        if not product:
            raise HTTPException(status_code=404, detail="Prodotto non trovato")

    return templates.TemplateResponse(request, "admin.html", {
        "active_tab":      "menu",
        "categories":      categories,
        "products":        products,
        "editing_product": product,
    })


@router.post("/admin/menu/product/{product_id}/edit")
def edit_product(
    product_id:    int,
    name:          str   = Form(...),
    description:   str   = Form(...),
    price:         float = Form(...),
    category_id:   int   = Form(...),
    image_url:     str   = Form(""),
    is_available:  Optional[str] = Form(None),
    is_featured:   Optional[str] = Form(None),
    is_vegetarian: Optional[str] = Form(None),
    is_spicy:      Optional[str] = Form(None),
    sort_order:    int   = Form(0),
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Prodotto non trovato")

        product.name          = name
        product.slug          = slugify(name)
        product.description   = description
        product.price         = price
        product.category_id   = category_id
        product.image_url     = image_url or None
        product.is_available  = is_available  == "on"
        product.is_featured   = is_featured   == "on"
        product.is_vegetarian = is_vegetarian == "on"
        product.is_spicy      = is_spicy      == "on"
        product.sort_order    = sort_order

        session.add(product)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)


@router.post("/admin/menu/product/{product_id}/delete")
def delete_product(
    product_id: int,
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Prodotto non trovato")
        session.delete(product)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)


@router.post("/admin/menu/product/{product_id}/toggle")
def toggle_availability(
    product_id: int,
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Prodotto non trovato")
        product.is_available = not product.is_available
        session.add(product)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)


@router.post("/admin/menu/category/add")
def add_category(
    name:       str = Form(...),
    sort_order: int = Form(0),
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        category = Category(
            name       = name,
            slug       = slugify(name),
            sort_order = sort_order,
        )
        session.add(category)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)


@router.post("/admin/menu/category/{category_id}/delete")
def delete_category(
    category_id: int,
    _admin: str = Depends(require_admin),
):
    with Session(engine) as session:
        products = session.exec(select(Product).where(Product.category_id == category_id)).all()
        if products:
            raise HTTPException(
                status_code=400,
                detail="Impossibile eliminare: ci sono prodotti in questa categoria"
            )
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Categoria non trovata")
        session.delete(category)
        session.commit()
    return RedirectResponse(url="/admin/menu", status_code=303)