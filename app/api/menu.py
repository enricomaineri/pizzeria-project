from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/menu", response_class=HTMLResponse)
def menu_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"title": "Menu | Vesuvio"}
    )
