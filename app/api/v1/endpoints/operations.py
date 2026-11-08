from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.auth_model import User, UserRole
from app.schemas.operations_schema import (
    FinishedGoodStockResponse,
    OperationsLogCreate,
    OperationsLogResponse,
    OperationsSummary,
)
from app.services.operations_service import OperationsService

router = APIRouter()

# RBAC: All roles (ADMIN, MANAGER, OPERATOR) can access operations
operations_guard = Depends(
    require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)
)


@router.post(
    "",
    response_model=OperationsLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[operations_guard],
)
async def log_operations_entry(
    payload: OperationsLogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Log production run, raw consumption, yield output, downtime, and increment stock."""
    service = OperationsService(db)
    return await service.log_operation(payload=payload, user_id=current_user.id)


@router.get(
    "",
    response_model=list[OperationsLogResponse],
    dependencies=[operations_guard],
)
async def list_operations_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    finished_product_name: str | None = Query(None),
):
    """List operational production logs."""
    service = OperationsService(db)
    return await service.list_operations(
        skip=skip, limit=limit, finished_product_name=finished_product_name
    )


@router.get(
    "/inventory",
    response_model=list[FinishedGoodStockResponse],
    dependencies=[operations_guard],
)
async def get_finished_goods_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """View real-time finished goods stock balances."""
    service = OperationsService(db)
    return await service.get_inventory_stock()


@router.get(
    "/summary",
    response_model=OperationsSummary,
    dependencies=[operations_guard],
)
async def get_operations_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """View aggregated production metrics, finished yields, and cumulative downtime."""
    service = OperationsService(db)
    return await service.get_summary_metrics()