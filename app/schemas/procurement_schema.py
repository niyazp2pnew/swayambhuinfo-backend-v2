import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.procurement_model import PaymentStatus


class ProcurementCreate(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=255)
    material_received: str = Field(..., min_length=1, max_length=255)
    quantity_received: str = Field(
        ...,
        description="Freeform text field: accommodates numbers, units, or manual notes",
    )
    vehicle_number: str = Field(..., min_length=1, max_length=50)
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    vendor_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    transport_amount: Decimal = Field(default=Decimal("0.00"), ge=0)

    gross_weight: Decimal = Field(..., ge=0)
    tare_weight: Decimal = Field(..., ge=0)
    moisture_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    remarks: str | None = None

    @model_validator(mode="after")
    def validate_weights(self) -> "ProcurementCreate":
        if self.gross_weight < self.tare_weight:
            raise ValueError("Gross weight cannot be less than tare weight.")
        return self


class ProcurementUpdate(BaseModel):
    vendor_name: str | None = None
    material_received: str | None = None
    quantity_received: str | None = None
    vehicle_number: str | None = None
    payment_status: PaymentStatus | None = None
    vendor_amount: Decimal | None = Field(None, ge=0)
    transport_amount: Decimal | None = Field(None, ge=0)
    gross_weight: Decimal | None = Field(None, ge=0)
    tare_weight: Decimal | None = Field(None, ge=0)
    moisture_percentage: Decimal | None = Field(None, ge=0, le=100)
    remarks: str | None = None


class ProcurementResponse(BaseModel):
    id: uuid.UUID
    vendor_name: str
    material_received: str
    quantity_received: str
    vehicle_number: str
    payment_status: PaymentStatus
    vendor_amount: Decimal
    transport_amount: Decimal
    gross_weight: Decimal
    tare_weight: Decimal
    moisture_percentage: Decimal
    net_weight: Decimal
    final_result_weight: Decimal
    remarks: str | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcurementSummary(BaseModel):
    total_entries: int
    total_gross_weight: Decimal
    total_final_result_weight: Decimal
    total_vendor_amount: Decimal
    total_transport_amount: Decimal
    unpaid_vendor_amount: Decimal