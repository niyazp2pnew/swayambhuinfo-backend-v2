import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.auth_model import UserRole
from app.models.storage import DocumentFolder, FolderDocument
from app.schemas.storage import DocumentResponse, FolderCreate, FolderResponse
from app.services.sales_service import SalesService

# Declare router instance
router = APIRouter()

# RBAC: Accessible by all roles for organizational and download tasks
folder_guard = Depends(
    require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)
)


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[folder_guard],
)
async def create_folder(
    payload: FolderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a categorized folder for invoices and tabular exports."""
    folder = DocumentFolder(
        name=payload.name.strip(),
        product_category=payload.product_category.strip()
        if payload.product_category
        else None,
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


@router.get(
    "",
    response_model=list[FolderResponse],
    dependencies=[folder_guard],
)
async def list_folders(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all created document folders."""
    res = await db.execute(select(DocumentFolder).order_by(DocumentFolder.name.asc()))
    return list(res.scalars().all())


@router.get(
    "/{folder_id}/documents",
    response_model=list[DocumentResponse],
    dependencies=[folder_guard],
)
async def list_folder_documents(
    folder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all invoices and files stored in a specific folder."""
    res = await db.execute(
        select(FolderDocument).where(FolderDocument.folder_id == folder_id)
    )
    return list(res.scalars().all())


@router.get(
    "/{folder_id}/export-csv",
    dependencies=[folder_guard],
)
async def export_folder_csv(
    folder_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Download tabular CSV export of all sales entries in this folder."""
    service = SalesService(db)
    csv_data = await service.export_folder_csv(folder_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=folder_{folder_id}.csv"},
    )