import uuid
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyUUIDMixin, TimestampMixin


class FinishedGoodsInventory(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "finished_goods_inventory"

    product_name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    available_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(50), nullable=False, default="KG"
    )


class OperationsLog(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "operations_logs"

    # Serial Number / Identifier
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    # Raw material consumed (links to procurement material name / freeform)
    raw_material_used: Mapped[str] = mapped_column(String(255), nullable=False)
    qty_raw_material_used: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Freeform string to accept manual notes or numbers

    # Finished product output
    finished_product_name: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    finished_product_qty: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # Machine Downtime
    downtime_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    downtime_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User Audit Trail
    logged_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    logged_by: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821