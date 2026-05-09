from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import (
    check_admin_credentials,
    create_session_token,
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    get_current_admin,
)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    # Se già loggato, vai direttamente all'admin
    if get_current_admin(request):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/admin/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if check_admin_credentials(username, password):
        token = create_session_token(username)
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            max_age=SESSION_MAX_AGE,
            httponly=True,   # non accessibile da JS
            samesite="lax",
        )
        return response

    return templates.TemplateResponse(request, "login.html", {
        "error": "Credenziali non valide. Riprova."
    })


@router.post("/admin/logout")
def logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response