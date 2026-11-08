import enum
import uuid
from decimal import Decimal
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PrimaryKeyUUIDMixin, TimestampMixin


class PaymentStatus(str, enum.Enum):
    PAID = "PAID"
    UNPAID = "UNPAID"


class ProcurementIntake(Base, PrimaryKeyUUIDMixin, TimestampMixin):
    __tablename__ = "procurement_intakes"

    # Vendor & Material (freeform manual fields)
    vendor_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    material_received: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_received: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Freeform string: accepts any custom text/units

    # Logistics & Financials
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.UNPAID,
    )
    vendor_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    transport_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # Weighbridge Measurements & Deduction
    gross_weight: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    tare_weight: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    moisture_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )

    # Computed Results
    net_weight: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    final_result_weight: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User Audit Trail
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_by: Mapped["User"] = relationship("User")  # type: ignore # noqa: F821