import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.auth_model import User, UserRole
from app.models.procurement_model import PaymentStatus
from app.schemas.procurement_schema import (
    ProcurementCreate,
    ProcurementResponse,
    ProcurementSummary,
    ProcurementUpdate,
)
from app.services.procurement_service import ProcurementService

router = APIRouter()

# RBAC Gate: ADMIN and MANAGER only
procurement_guard = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))


@router.post(
    "",
    response_model=ProcurementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[procurement_guard],
)
async def create_intake_entry(
    payload: ProcurementCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Log inward procurement & weighbridge intake with automated deductions."""
    service = ProcurementService(db)
    return await service.create_entry(payload=payload, user_id=current_user.id)


@router.get(
    "",
    response_model=list[ProcurementResponse],
    dependencies=[procurement_guard],
)
async def list_intake_entries(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    vendor_name: str | None = Query(None),
    payment_status: PaymentStatus | None = Query(None),
):
    """Retrieve historical procurement logs with optional filters."""
    service = ProcurementService(db)
    return await service.list_entries(
        skip=skip,
        limit=limit,
        vendor_name=vendor_name,
        payment_status=payment_status,
    )


@router.get(
    "/summary",
    response_model=ProcurementSummary,
    dependencies=[procurement_guard],
)
async def get_procurement_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve aggregate procurement analytics, net yields, and liabilities."""
    service = ProcurementService(db)
    return await service.get_summary_metrics()


@router.get(
    "/{entry_id}",
    response_model=ProcurementResponse,
    dependencies=[procurement_guard],
)
async def get_intake_entry(
    entry_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Fetch details of a single procurement intake record."""
    service = ProcurementService(db)
    return await service.get_by_id(entry_id)


@router.patch(
    "/{entry_id}",
    response_model=ProcurementResponse,
    dependencies=[procurement_guard],
)
async def update_intake_entry(
    entry_id: uuid.UUID,
    payload: ProcurementUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update manual intake entries and recalculate net weights if adjusted."""
    service = ProcurementService(db)
    return await service.update_entry(entry_id=entry_id, payload=payload)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],  # Deletions restricted to ADMIN
)
async def delete_intake_entry(
    entry_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an intake entry (Admin only)."""
    service = ProcurementService(db)
    await service.delete_entry(entry_id)