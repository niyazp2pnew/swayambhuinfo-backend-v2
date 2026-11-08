from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyUUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.auth_model import User
    from app.models.storage import DocumentFolder


class SalesEntry(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "sales_entries"

    # Customized Bill Number
    bill_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    # Buyer Contact Information
    buyer_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    buyer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    buyer_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Product & Inventory
    finished_good_name: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    quantity_sold: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Pricing & GST
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gst_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    pdf_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Folder Association
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_folders.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    folder: Mapped["DocumentFolder | None"] = relationship(
        "DocumentFolder", back_populates="sales_entries"
    )
    created_by: Mapped["User"] = relationship("User")