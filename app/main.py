from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import router
from app.api.orders import router as orders_router
from app.api.admin import router as admin_router
from app.api.auth_routes import router as auth_router
from app.db import create_db_and_tables
from app.seed import seed_data

app = FastAPI(title="Pizzeria Project")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_data()