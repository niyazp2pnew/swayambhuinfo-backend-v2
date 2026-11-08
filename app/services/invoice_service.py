import io
import os
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.sales_model import SalesEntry


class InvoiceService:
    @staticmethod
    def generate_sales_receipt_pdf(entry: SalesEntry) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#063D2A"),
        )
        subtitle_style = ParagraphStyle(
            "SubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
        )
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.whitesmoke,
        )
        cell_style = ParagraphStyle(
            "Cell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748"),
        )

        story = []

        # Corporate Header
        story.append(Paragraph("SWAYAMBHU INNOVATIVE SOLUTIONS", title_style))
        story.append(Paragraph("Official Sales Receipt & Tax Manifest", subtitle_style))
        story.append(Spacer(1, 15))

        # Metadata Table
        meta_data = [
            [
                Paragraph(f"<b>Bill Number:</b> {entry.bill_number}", cell_style),
                Paragraph(f"<b>Sale Date:</b> {entry.sale_date}", cell_style),
            ],
            [
                Paragraph(f"<b>Buyer Name:</b> {entry.buyer_name}", cell_style),
                Paragraph(f"<b>Buyer Phone:</b> {entry.buyer_phone}", cell_style),
            ],
            [
                Paragraph(f"<b>Buyer Email:</b> {entry.buyer_email}", cell_style),
                Paragraph(f"<b>Product:</b> {entry.finished_good_name}", cell_style),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAF9")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Items & Billing Table
        items_data = [
            [
                Paragraph("<b>Description</b>", header_style),
                Paragraph("<b>Qty (KG)</b>", header_style),
                Paragraph("<b>Rate (INR)</b>", header_style),
                Paragraph("<b>Taxable (INR)</b>", header_style),
                Paragraph("<b>GST %</b>", header_style),
                Paragraph("<b>Total (INR)</b>", header_style),
            ],
            [
                Paragraph(entry.finished_good_name, cell_style),
                Paragraph(f"{entry.quantity_sold:.2f}", cell_style),
                Paragraph(f"{entry.rate:.2f}", cell_style),
                Paragraph(f"{entry.taxable_amount:.2f}", cell_style),
                Paragraph(f"{entry.gst_percentage:.2f}%", cell_style),
                Paragraph(f"{entry.total_amount:.2f}", cell_style),
            ],
        ]

        items_table = Table(
            items_data, colWidths=[150, 75, 75, 80, 60, 100]
        )
        items_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#063D2A")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(items_table)
        story.append(Spacer(1, 15))

        # Financial Summary Table
        summary_data = [
            [Paragraph("Taxable Amount:", cell_style), Paragraph(f"INR {entry.taxable_amount:.2f}", cell_style)],
            [Paragraph(f"GST Amount ({entry.gst_percentage:.1f}%):", cell_style), Paragraph(f"INR {entry.gst_amount:.2f}", cell_style)],
            [Paragraph("<b>Grand Total:</b>", cell_style), Paragraph(f"<b>INR {entry.total_amount:.2f}</b>", cell_style)],
        ]
        summary_table = Table(summary_data, colWidths=[120, 100], hAlign="RIGHT")
        summary_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(summary_table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()