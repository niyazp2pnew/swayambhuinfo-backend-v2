import uuid
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operations_model import FinishedGoodsInventory, OperationsLog
from app.schemas.operations_schema import (
    OperationsLogCreate,
    OperationsSummary,
)


class OperationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_operation(
        self, payload: OperationsLogCreate, user_id: uuid.UUID
    ) -> OperationsLog:
        # 1. Prevent duplicate S.No
        existing_sno = await self.db.execute(
            select(OperationsLog).where(
                OperationsLog.serial_number == payload.serial_number.strip()
            )
        )
        if existing_sno.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Serial Number / Run ID '{payload.serial_number}' already exists.",
            )

        # 2. Register operation run
        prod_name = payload.finished_product_name.strip()
        log_entry = OperationsLog(
            serial_number=payload.serial_number.strip(),
            raw_material_used=payload.raw_material_used.strip(),
            qty_raw_material_used=payload.qty_raw_material_used.strip(),
            finished_product_name=prod_name,
            finished_product_qty=payload.finished_product_qty,
            downtime_minutes=payload.downtime_minutes,
            downtime_reason=payload.downtime_reason,
            logged_by_id=user_id,
        )
        self.db.add(log_entry)

        # 3. Atomically upsert finished goods inventory stock
        stock_query = await self.db.execute(
            select(FinishedGoodsInventory)
            .where(FinishedGoodsInventory.product_name == prod_name)
            .with_for_update()
        )
        stock_item = stock_query.scalar_one_or_none()

        if stock_item:
            stock_item.available_quantity += payload.finished_product_qty
        else:
            stock_item = FinishedGoodsInventory(
                product_name=prod_name,
                available_quantity=payload.finished_product_qty,
                unit_of_measure="KG",
            )
            self.db.add(stock_item)

        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

    async def list_operations(
        self,
        skip: int = 0,
        limit: int = 100,
        finished_product_name: str | None = None,
    ) -> list[OperationsLog]:
        query = select(OperationsLog).order_by(desc(OperationsLog.created_at))
        if finished_product_name:
            query = query.where(
                OperationsLog.finished_product_name.ilike(
                    f"%{finished_product_name}%"
                )
            )
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_inventory_stock(self) -> list[FinishedGoodsInventory]:
        query = select(FinishedGoodsInventory).order_by(
            FinishedGoodsInventory.product_name.asc()
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_summary_metrics(self) -> OperationsSummary:
        query = select(
            func.count(OperationsLog.id).label("total_runs"),
            func.coalesce(func.sum(OperationsLog.finished_product_qty), 0).label(
                "total_finished"
            ),
            func.coalesce(func.sum(OperationsLog.downtime_minutes), 0).label(
                "total_downtime"
            ),
            func.count(func.distinct(OperationsLog.finished_product_name)).label(
                "distinct_products"
            ),
        )
        result = await self.db.execute(query)
        row = result.one()

        return OperationsSummary(
            total_runs=row.total_runs,
            total_finished_goods_produced=Decimal(str(row.total_finished)),
            total_downtime_minutes=int(row.total_downtime),
            distinct_products_count=int(row.distinct_products),
        )