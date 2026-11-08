import os
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.auth_model import User, UserRole
from app.models.sales_model import SalesEntry
from app.schemas.sales_schema import SalesEntryCreate, SalesEntryResponse
from app.services.sales_service import SalesService

router = APIRouter()

# RBAC: ADMIN and OPERATOR manage Sales / Invoices
sales_guard = Depends(require_roles(UserRole.ADMIN, UserRole.OPERATOR))


@router.post(
    "",
    response_model=SalesEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[sales_guard],
)
async def create_sales_order(
    payload: SalesEntryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates sales entry, auto-deducts finished inventory stock, and renders PDF receipt."""
    service = SalesService(db)
    return await service.create_sales_entry(payload=payload, user_id=current_user.id)


@router.get(
    "",
    response_model=list[SalesEntryResponse],
    dependencies=[sales_guard],
)
async def list_sales_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve historical sales orders."""
    service = SalesService(db)
    return await service.list_sales(skip=skip, limit=limit)


@router.get(
    "/{sales_id}/pdf",
    dependencies=[sales_guard],
)
async def download_invoice_pdf(
    sales_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download official Sales Receipt PDF with in-memory fallback for ephemeral cloud hosting."""
    entry = await db.get(SalesEntry, sales_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sales entry '{sales_id}' not found.",
        )

    # 1. Serve from disk if file is still cached locally
    if entry.pdf_file_path and os.path.exists(entry.pdf_file_path):
        return FileResponse(
            entry.pdf_file_path,
            media_type="application/pdf",
            filename=f"{entry.bill_number}.pdf",
        )

    # 2. Resilient Fallback: Generate the ReportLab PDF in-memory from database values
    pdf_bytes = InvoiceService.generate_sales_receipt_pdf(entry)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={entry.bill_number}.pdf"
        },
    )