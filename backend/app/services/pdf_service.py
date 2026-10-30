import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.report import GeneratedReport

class ReportPdfGenerator:
    """
    Generates professional PDF financial reports using ReportLab.
    """

    @staticmethod
    def generate_pdf(report: GeneratedReport) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F2942"),
            spaceAfter=4,
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#5A6B82"),
            spaceAfter=12
        )
        section_style = ParagraphStyle(
            "DocSection",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F2942"),
            spaceBefore=14,
            spaceAfter=8,
            fontName="Helvetica-Bold"
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B")
        )
        muted_style = ParagraphStyle(
            "DocMuted",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B")
        )

        story = []

        # 1. Header & Title
        story.append(Paragraph(report.title, title_style))
        gen_time = report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if report.created_at else "N/A"
        period_text = f"Period: <b>{report.start_date.isoformat()}</b> to <b>{report.end_date.isoformat()}</b> &nbsp;|&nbsp; Currency: <b>{report.currency}</b> &nbsp;|&nbsp; Generated: <b>{gen_time}</b>"
        story.append(Paragraph(period_text, subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceAfter=14))

        # Parse stored JSON payloads
        params = json.loads(report.report_parameters or "{}")
        summary = json.loads(report.summary_metrics or "{}")
        details = json.loads(report.detailed_data or "{}")

        # 2. Key Executive Summary Metrics Table
        story.append(Paragraph("Executive Financial Summary", section_style))
        
        summary_rows = [["Metric", "Value"]]
        for k, v in summary.items():
            clean_key = k.replace("_", " ").title()
            if isinstance(v, (int, float)):
                if "pct" in k or "margin" in k or "ratio" in k:
                    val_str = f"{v:.2f}%"
                elif "count" in k:
                    val_str = f"{int(v):,}"
                else:
                    val_str = f"{report.currency} {v:,.2f}"
            elif v is None:
                val_str = "N/A"
            else:
                val_str = str(v)
            summary_rows.append([clean_key, val_str])

        summary_table = Table(summary_rows, colWidths=[260, 260])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F2942")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 14))

        # 3. Monthly Breakdown Table (if available)
        monthly_data = details.get("monthly_breakdown", [])
        if monthly_data:
            story.append(Paragraph("Monthly Performance Trends", section_style))
            m_rows = [["Period", "Income", "Expenses", "Net Movement", "Txs"]]
            for row in monthly_data:
                m_rows.append([
                    row.get("period", ""),
                    f"{report.currency} {row.get('income', 0):,.2f}",
                    f"{report.currency} {row.get('expense', 0):,.2f}",
                    f"{report.currency} {row.get('net', 0):,.2f}",
                    str(row.get("transaction_count", 0))
                ])
            
            m_table = Table(m_rows, colWidths=[90, 115, 115, 130, 70])
            m_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284C7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
            ]))
            story.append(m_table)
            story.append(Spacer(1, 14))

        # 4. Category Breakdown Table (if available)
        cat_data = details.get("categories") or details.get("expense_categories") or details.get("income_categories")
        if cat_data:
            story.append(Paragraph("Category Distribution", section_style))
            c_rows = [["Category", "Type", "Total Outlay / Inflow", "Share (%)"]]
            for cat in cat_data[:12]:  # Top 12 categories
                c_rows.append([
                    cat.get("category_name", ""),
                    cat.get("category_type", ""),
                    f"{report.currency} {cat.get('total_amount', 0):,.2f}",
                    f"{cat.get('percentage', 0):.1f}%"
                ])
            c_table = Table(c_rows, colWidths=[180, 100, 160, 80])
            c_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            story.append(c_table)
            story.append(Spacer(1, 14))

        # 5. Calculation Notes, Methodology & Disclaimers
        story.append(KeepTogether([
            Paragraph("Calculation Methodology & Assumptions", section_style),
            Paragraph(params.get("methodology", "Standard accounting aggregation."), body_style),
            Spacer(1, 6),
            Paragraph(
                "<b>Compliance Notice:</b> This report is generated programmatically from transaction records recorded in the Smart Financial Reporting Tool. "
                "Figures should be verified alongside official bank statements and audited accounting schedules.",
                muted_style
            )
        ]))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
