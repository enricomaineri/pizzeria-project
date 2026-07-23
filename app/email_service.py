import logging
from typing import List

import httpx

from app.config import EMAIL_FROM, RESEND_API_KEY
from app.db_models import Order
from app.templates_config import templates

logger = logging.getLogger("pizzeria")

RESEND_API_URL = "https://api.resend.com/emails"


def send_order_receipt(order: Order, items: List[dict]) -> None:
    """Invia la ricevuta ordine via email tramite Resend.
    Chiamata come BackgroundTask: non deve mai far fallire la creazione
    dell'ordine, quindi ogni errore viene solo loggato."""
    if not RESEND_API_KEY or not EMAIL_FROM:
        logger.warning(
            "Ricevuta non inviata per ordine #%s: RESEND_API_KEY o EMAIL_FROM non configurati.",
            order.id,
        )
        return

    html = templates.env.get_template("email_receipt.html").render(
        order=order, items=items
    )

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": EMAIL_FROM,
                "to": [order.customer_email],
                "subject": f"Vesuvio — Conferma ordine #{order.id}",
                "html": html,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("Ricevuta inviata per ordine #%s a %s", order.id, order.customer_email)
    except httpx.HTTPError:
        logger.exception("Invio ricevuta fallito per ordine #%s", order.id)
