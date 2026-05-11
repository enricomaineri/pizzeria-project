import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.api.router import router
from app.api.orders import router as orders_router
from app.api.admin import router as admin_router
from app.api.auth_routes import router as auth_router
from app.db import create_db_and_tables
from app.seed import seed_data

logger = logging.getLogger("pizzeria")

app = FastAPI(title="Pizzeria Project")

# Registra il limiter e il suo error handler sull'app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(auth_router)


# ── Errori di validazione Pydantic (422) ────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for e in errors:
        field = " → ".join(str(loc) for loc in e["loc"] if loc != "body")
        msg = e["msg"]
        messages.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(
        status_code=422,
        content={"detail": messages}
    )


# ── Errori HTTP generici (4xx / 5xx) ───────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail or "Errore nella richiesta"}
        )
    if exc.status_code in (401, 403):
        return RedirectResponse(url="/admin/login", status_code=302)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "Errore"}
    )


# ── Catch-all: eccezioni non gestite (500) ──────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Eccezione non gestita su %s", request.url.path)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Errore interno del server. Riprova tra qualche istante."}
        )
    return RedirectResponse(url="/admin", status_code=302)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()
