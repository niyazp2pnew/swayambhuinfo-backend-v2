import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class OperationsLogCreate(BaseModel):
    serial_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Manual S.No or unique run ID",
    )
    raw_material_used: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Raw material name matching intake or custom raw entry",
    )
    qty_raw_material_used: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Manual text quantity of raw material consumed",
    )
    finished_product_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Finished good produced (e.g. HDPE Bales, Granules, Eco-Board)",
    )
    finished_product_qty: Decimal = Field(
        ...,
        gt=0,
        description="Numeric finished quantity credited to finished goods inventory",
    )
    downtime_minutes: int = Field(default=0, ge=0)
    downtime_reason: str | None = None


class OperationsLogResponse(BaseModel):
    id: uuid.UUID
    serial_number: str
    raw_material_used: str
    qty_raw_material_used: str
    finished_product_name: str
    finished_product_qty: Decimal
    downtime_minutes: int
    downtime_reason: str | None
    logged_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinishedGoodStockResponse(BaseModel):
    id: uuid.UUID
    product_name: str
    available_quantity: Decimal
    unit_of_measure: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationsSummary(BaseModel):
    total_runs: int
    total_finished_goods_produced: Decimal
    total_downtime_minutes: int
    distinct_products_count: int