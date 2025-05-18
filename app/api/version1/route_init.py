from fastapi import APIRouter
from app.api.routes.auth.register import router as register_router
from app.api.routes.auth.login import router as login_router
from app.api.routes.auth.magic_link import router as magic_link_router
from app.api.routes.auth.google import router as google_router
from app.api.routes.auth.refresh import router as refresh_router
from app.api.routes.dashboard.upload_product import router as supplier_product_routes
from app.api.routes.dashboard.dashboard import router as dashboard_routes
from app.api.routes.product.product import router as product_routes


router = APIRouter()
router.include_router(register_router,prefix="/auth", tags=["Auth"])
router.include_router(login_router,prefix="/auth", tags=["Auth"])
router.include_router(magic_link_router,prefix="/auth", tags=["Auth"])
router.include_router(google_router,prefix="/auth", tags=["Auth"])
router.include_router(refresh_router,prefix="/auth", tags=["Auth"])
router.include_router(supplier_product_routes,prefix="/dashboard", tags=["Dashboard"])
router.include_router(dashboard_routes,prefix="/dashboard", tags=["Dashboard"])
router.include_router(product_routes, tags=["Product"])





