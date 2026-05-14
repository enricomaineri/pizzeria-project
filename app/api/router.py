from fastapi import APIRouter

from app.api.public import router as public_router
from app.api.menu import router as menu_router
from app.api.contact import router as contact_router
from app.api.orders import router as orders_router
from app.api.admin import router as admin_router
from app.api.auth_routes import router as auth_router

router = APIRouter()

router.include_router(public_router)
router.include_router(menu_router)
router.include_router(contact_router)
router.include_router(orders_router)
router.include_router(admin_router)
router.include_router(auth_router)
