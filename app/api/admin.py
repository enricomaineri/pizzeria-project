from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import engine
from app.db_models import Order, OrderItem

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, status: str | None = None):
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    start_of_next_day = start_of_day + timedelta(days=1)

    with Session(engine) as session:
        today_orders = session.exec(
            select(Order).where(
                Order.created_at >= start_of_day,
                Order.created_at < start_of_next_day
            )
        ).all()

        pending_count = len([o for o in today_orders if o.status == "pending"])
        confirmed_count = len([o for o in today_orders if o.status == "confirmed"])
        preparing_count = len([o for o in today_orders if o.status == "preparing"])
        ready_count = len([o for o in today_orders if o.status == "ready"])
        delivered_count = len([o for o in today_orders if o.status == "delivered"])

        statement = select(Order).order_by(Order.created_at.desc())

        if status:
            statement = (
                select(Order)
                .where(Order.status == status)
                .order_by(Order.created_at.desc())
            )

        orders = session.exec(statement).all()

        orders_with_items = []
        for order in orders:
            items = session.exec(
                select(OrderItem).where(OrderItem.order_id == order.id)
            ).all()

            orders_with_items.append({
                "order": order,
                "items": items
            })

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "orders_with_items": orders_with_items,
            "selected_status": status,
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "preparing_count": preparing_count,
            "ready_count": ready_count,
            "delivered_count": delivered_count
        }
    )


@router.post("/admin/order/{order_id}/status")
def update_order_status(order_id: int, status: str = Form(...)):
    with Session(engine) as session:
        order = session.get(Order, order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Ordine non trovato")

        order.status = status
        session.add(order)
        session.commit()

    return RedirectResponse(url="/admin", status_code=303)