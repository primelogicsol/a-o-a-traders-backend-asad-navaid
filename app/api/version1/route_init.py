from fastapi import APIRouter
from app.api.routes.auth.register import router as register_router
from app.api.routes.auth.login import router as login_router
from app.api.routes.auth.magic_link import router as magic_link_router
from app.api.routes.auth.google import router as google_router
from app.api.routes.auth.refresh import router as refresh_router

router = APIRouter()
router.include_router(register_router)
router.include_router(login_router)
router.include_router(magic_link_router)
router.include_router(google_router)
router.include_router(refresh_router)



