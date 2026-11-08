import csv
import io
import os
import uuid
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.operations_model import FinishedGoodsInventory
from app.models.sales_model import SalesEntry
from app.models.storage import DocumentFolder, DocumentType, FolderDocument
from app.schemas.sales_schema import SalesEntryCreate
from app.services.invoice_service import InvoiceService


class SalesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sales_entry(
        self, payload: SalesEntryCreate, user_id: uuid.UUID
    ) -> SalesEntry:
        # 1. Check duplicate Bill Number
        existing_bill = await self.db.execute(
            select(SalesEntry).where(SalesEntry.bill_number == payload.bill_number.strip())
        )
        if existing_bill.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bill Number '{payload.bill_number}' already exists.",
            )

        # 2. Concurrency-Safe Stock Lock & Deduction
        stock_query = await self.db.execute(
            select(FinishedGoodsInventory)
            .where(FinishedGoodsInventory.product_name == payload.finished_good_name.strip())
            .with_for_update()
        )
        stock_item = stock_query.scalar_one_or_none()

        if not stock_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Finished Good '{payload.finished_good_name}' does not exist in inventory.",
            )

        if stock_item.available_quantity < payload.quantity_sold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient inventory for '{payload.finished_good_name}'. "
                    f"Available: {stock_item.available_quantity:.2f}, Requested: {payload.quantity_sold:.2f}"
                ),
            )

        # Deduct quantity from stock
        stock_item.available_quantity -= payload.quantity_sold

        # 3. Financial Computations
        taxable_amt = (payload.quantity_sold * payload.rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        gst_amt = (taxable_amt * (payload.gst_percentage / Decimal("100.00"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_amt = (taxable_amt + gst_amt).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        sales_record = SalesEntry(
            bill_number=payload.bill_number.strip(),
            buyer_name=payload.buyer_name.strip(),
            buyer_phone=payload.buyer_phone.strip(),
            buyer_email=payload.buyer_email.strip(),
            finished_good_name=payload.finished_good_name.strip(),
            quantity_sold=payload.quantity_sold,
            rate=payload.rate,
            taxable_amount=taxable_amt,
            gst_percentage=payload.gst_percentage,
            gst_amount=gst_amt,
            total_amount=total_amt,
            sale_date=payload.sale_date,
            folder_id=payload.folder_id,
            created_by_id=user_id,
        )
        self.db.add(sales_record)
        await self.db.flush()

        # 4. Generate & Save PDF Document
        pdf_bytes = InvoiceService.generate_sales_receipt_pdf(sales_record)
        target_dir = os.path.join(
            settings.STORAGE_DIR,
            "invoices",
            str(payload.folder_id) if payload.folder_id else "unassigned",
        )
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{sales_record.bill_number}.pdf"
        file_path = os.path.join(target_dir, filename)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        sales_record.pdf_file_path = file_path

        # If linked to a folder, register the document entry
        if payload.folder_id:
            doc_entry = FolderDocument(
                folder_id=payload.folder_id,
                document_name=filename,
                file_type=DocumentType.PDF,
                file_path=file_path,
            )
            self.db.add(doc_entry)

        await self.db.commit()
        await self.db.refresh(sales_record)
        return sales_record

    async def list_sales(self, skip: int = 0, limit: int = 100) -> list[SalesEntry]:
        query = (
            select(SalesEntry)
            .order_by(desc(SalesEntry.sale_date), desc(SalesEntry.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def export_folder_csv(self, folder_id: uuid.UUID) -> str:
        """Compiles all sales records belonging to a folder into tabular CSV data."""
        query = (
            select(SalesEntry)
            .where(SalesEntry.folder_id == folder_id)
            .order_by(desc(SalesEntry.sale_date))
        )
        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Bill Number",
            "Sale Date",
            "Buyer Name",
            "Buyer Phone",
            "Buyer Email",
            "Product Name",
            "Quantity Sold",
            "Rate",
            "Taxable Amount",
            "GST %",
            "GST Amount",
            "Total Amount",
        ])

        for e in entries:
            writer.writerow([
                e.bill_number,
                str(e.sale_date),
                e.buyer_name,
                e.buyer_phone,
                e.buyer_email,
                e.finished_good_name,
                f"{e.quantity_sold:.2f}",
                f"{e.rate:.2f}",
                f"{e.taxable_amount:.2f}",
                f"{e.gst_percentage:.2f}",
                f"{e.gst_amount:.2f}",
                f"{e.total_amount:.2f}",
            ])

        return output.getvalue()