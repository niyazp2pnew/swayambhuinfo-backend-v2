import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SalesEntryCreate(BaseModel):
    bill_number: str = Field(..., min_length=1, max_length=100)
    buyer_name: str = Field(..., min_length=1, max_length=255)
    buyer_phone: str = Field(..., min_length=5, max_length=30)
    buyer_email: EmailStr
    finished_good_name: str = Field(..., min_length=1, max_length=255)
    quantity_sold: Decimal = Field(..., gt=0)
    rate: Decimal = Field(..., gt=0)
    gst_percentage: Decimal = Field(..., ge=0, le=100)
    sale_date: date
    folder_id: uuid.UUID | None = None


class SalesEntryResponse(BaseModel):
    id: uuid.UUID
    bill_number: str
    buyer_name: str
    buyer_phone: str
    buyer_email: EmailStr
    finished_good_name: str
    quantity_sold: Decimal
    rate: Decimal
    taxable_amount: Decimal
    gst_percentage: Decimal
    gst_amount: Decimal
    total_amount: Decimal
    sale_date: date
    pdf_file_path: str | None
    folder_id: uuid.UUID | None
    created_by_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)