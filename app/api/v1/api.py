from fastapi import APIRouter
from app.api.v1.endpoints import auth, procurement, operations, sales, folders

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(
    procurement.router, prefix="/procurement", tags=["Procurement & Intake"]
)
api_router.include_router(
    operations.router, prefix="/operations", tags=["Operations & Inventory Yield"]
)

api_router.include_router(
    sales.router, prefix="/sales", tags=["Sales & Invoicing"]
)
api_router.include_router(
    folders.router, prefix="/folders", tags=["Folder & Document Management"]
)