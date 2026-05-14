from fastapi import APIRouter
from app.api.public import router as public_router
from app.api.menu import router as menu_router
from app.api.contact import router as contact_router

router = APIRouter()

router.include_router(public_router)
router.include_router(menu_router)
router.include_router(contact_router)
