from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyUUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.sales_model import SalesEntry


class DocumentType(str, enum.Enum):
    PDF = "PDF"
    CSV = "CSV"


class DocumentFolder(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "document_folders"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    product_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships using string targets to prevent circular runtime imports
    sales_entries: Mapped[list["SalesEntry"]] = relationship(
        "SalesEntry", back_populates="folder"
    )
    documents: Mapped[list["FolderDocument"]] = relationship(
        "FolderDocument", back_populates="folder", cascade="all, delete-orphan"
    )


class FolderDocument(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "folder_documents"

    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_folders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[DocumentType] = mapped_column(
        String(10), nullable=False, default=DocumentType.PDF
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    folder: Mapped["DocumentFolder"] = relationship(
        "DocumentFolder", back_populates="documents"
    )