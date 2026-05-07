from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/contatti", response_class=HTMLResponse)
def contact_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={"title": "Contatti | Vesuvio"}
    )