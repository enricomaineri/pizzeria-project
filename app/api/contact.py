from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templates_config import templates

router = APIRouter()


@router.get("/contatti", response_class=HTMLResponse)
def contact_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={"title": "Contatti | Vesuvio"}
    )