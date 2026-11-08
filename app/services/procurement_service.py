import uuid
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement_model import PaymentStatus, ProcurementIntake
from app.schemas.procurement_schema import (
    ProcurementCreate,
    ProcurementSummary,
    ProcurementUpdate,
)


class ProcurementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def calculate_weights(
        gross: Decimal, tare: Decimal, moisture_pct: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        Net Weight = Gross - Tare
        Final Result = Net Weight * (1 - (Moisture% / 100))
        """
        net = gross - tare
        multiplier = Decimal("1.00") - (moisture_pct / Decimal("100.00"))
        final_result = (net * multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return net, final_result

    async def create_entry(
        self, payload: ProcurementCreate, user_id: uuid.UUID
    ) -> ProcurementIntake:
        net_wt, final_wt = self.calculate_weights(
            gross=payload.gross_weight,
            tare=payload.tare_weight,
            moisture_pct=payload.moisture_percentage,
        )

        entry = ProcurementIntake(
            vendor_name=payload.vendor_name.strip(),
            material_received=payload.material_received.strip(),
            quantity_received=payload.quantity_received.strip(),
            vehicle_number=payload.vehicle_number.strip().upper(),
            payment_status=payload.payment_status,
            vendor_amount=payload.vendor_amount,
            transport_amount=payload.transport_amount,
            gross_weight=payload.gross_weight,
            tare_weight=payload.tare_weight,
            moisture_percentage=payload.moisture_percentage,
            net_weight=net_wt,
            final_result_weight=final_wt,
            remarks=payload.remarks,
            created_by_id=user_id,
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def list_entries(
        self,
        skip: int = 0,
        limit: int = 100,
        vendor_name: str | None = None,
        payment_status: PaymentStatus | None = None,
    ) -> list[ProcurementIntake]:
        query = select(ProcurementIntake).order_by(
            desc(ProcurementIntake.created_at)
        )

        if vendor_name:
            query = query.where(
                ProcurementIntake.vendor_name.ilike(f"%{vendor_name}%")
            )
        if payment_status:
            query = query.where(ProcurementIntake.payment_status == payment_status)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, entry_id: uuid.UUID) -> ProcurementIntake:
        entry = await self.db.get(ProcurementIntake, entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Procurement record '{entry_id}' not found.",
            )
        return entry

    async def update_entry(
        self, entry_id: uuid.UUID, payload: ProcurementUpdate
    ) -> ProcurementIntake:
        entry = await self.get_by_id(entry_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in ["vendor_name", "material_received", "quantity_received"]:
                setattr(entry, field, value.strip())
            elif field == "vehicle_number":
                setattr(entry, field, value.strip().upper())
            else:
                setattr(entry, field, value)

        # Recalculate weights if any related parameters were modified
        if any(
            k in update_data
            for k in ["gross_weight", "tare_weight", "moisture_percentage"]
        ):
            if entry.gross_weight < entry.tare_weight:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Updated gross weight cannot be less than tare weight.",
                )
            net_wt, final_wt = self.calculate_weights(
                gross=entry.gross_weight,
                tare=entry.tare_weight,
                moisture_pct=entry.moisture_percentage,
            )
            entry.net_weight = net_wt
            entry.final_result_weight = final_wt

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete_entry(self, entry_id: uuid.UUID) -> None:
        entry = await self.get_by_id(entry_id)
        await self.db.delete(entry)
        await self.db.commit()

    async def get_summary_metrics(self) -> ProcurementSummary:
        query = select(
            func.count(ProcurementIntake.id).label("total_entries"),
            func.coalesce(func.sum(ProcurementIntake.gross_weight), 0).label(
                "total_gross"
            ),
            func.coalesce(
                func.sum(ProcurementIntake.final_result_weight), 0
            ).label("total_final"),
            func.coalesce(func.sum(ProcurementIntake.vendor_amount), 0).label(
                "total_vendor"
            ),
            func.coalesce(func.sum(ProcurementIntake.transport_amount), 0).label(
                "total_transport"
            ),
            func.coalesce(
                func.sum(
                    ProcurementIntake.vendor_amount
                ).filter(ProcurementIntake.payment_status == PaymentStatus.UNPAID),
                0,
            ).label("unpaid_vendor"),
        )
        result = await self.db.execute(query)
        row = result.one()

        return ProcurementSummary(
            total_entries=row.total_entries,
            total_gross_weight=Decimal(str(row.total_gross)),
            total_final_result_weight=Decimal(str(row.total_final)),
            total_vendor_amount=Decimal(str(row.total_vendor)),
            total_transport_amount=Decimal(str(row.total_transport)),
            unpaid_vendor_amount=Decimal(str(row.unpaid_vendor)),
        )