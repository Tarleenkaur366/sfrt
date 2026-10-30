import json
import io
import csv
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.report import GeneratedReport
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
    VALID_REPORT_TYPES
)
from app.routers.deps import get_current_user
from app.services.reporting_engine import SmartReportingEngine
from app.services.pdf_service import ReportPdfGenerator
from app.services.audit_service import AuditService
from app.utils.csv_sanitizer import sanitize_csv_cell

router = APIRouter(prefix="/reports", tags=["Reports"])

def map_report_response(r: GeneratedReport) -> ReportResponse:
    params = json.loads(r.report_parameters) if r.report_parameters else None
    summary = json.loads(r.summary_metrics) if r.summary_metrics else None
    details = json.loads(r.detailed_data) if r.detailed_data else None

    return ReportResponse(
        id=r.id,
        user_id=r.user_id,
        report_type=r.report_type,
        title=r.title,
        start_date=r.start_date,
        end_date=r.end_date,
        currency=r.currency,
        report_parameters=params,
        summary_metrics=summary,
        detailed_data=details,
        generation_status=r.generation_status,
        notes=r.notes,
        created_at=r.created_at
    )

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    req: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.report_type not in VALID_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Allowed types: {', '.join(VALID_REPORT_TYPES)}"
        )

    if req.end_date < req.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be earlier than or equal to end date."
        )

    curr = req.currency.upper() if req.currency else current_user.default_currency or "INR"

    report = SmartReportingEngine.generate_report(
        db=db,
        user_id=current_user.id,
        report_type=req.report_type,
        start_date=req.start_date,
        end_date=req.end_date,
        currency=curr,
        title=req.title,
        category_ids=req.category_ids,
        transaction_types=req.transaction_types,
        opening_cash_balance=req.opening_cash_balance or 0.0,
        notes=req.notes
    )

    AuditService.log(db, current_user.id, "REPORT_GENERATE", "REPORT", report.id, f"Generated {report.report_type} report: '{report.title}'")
    return map_report_response(report)

@router.get("", response_model=ReportListResponse)
def list_reports(
    report_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(GeneratedReport).filter(GeneratedReport.user_id == current_user.id)
    if report_type:
        query = query.filter(GeneratedReport.report_type == report_type)

    reports = query.order_by(desc(GeneratedReport.created_at)).all()
    return ReportListResponse(
        items=[map_report_response(r) for r in reports],
        total=len(reports)
    )

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(GeneratedReport).filter(
        GeneratedReport.id == report_id,
        GeneratedReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return map_report_response(report)

@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query("pdf"),  # 'pdf' or 'csv'
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(GeneratedReport).filter(
        GeneratedReport.id == report_id,
        GeneratedReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    clean_title = "".join(c for c in report.title if c.isalnum() or c in ("-", "_")).rstrip()
    
    if format.lower() == "pdf":
        try:
            pdf_bytes = ReportPdfGenerator.generate_pdf(report)
            filename = f"{clean_title}_{report.id[:8]}.pdf"
            AuditService.log(db, current_user.id, "EXPORT_PDF", "REPORT", report.id, f"Downloaded PDF for report '{report.title}'")
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {str(e)}")

    elif format.lower() == "csv":
        # Export as comprehensive CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Report Title", sanitize_csv_cell(report.title)])
        writer.writerow(["Report Type", sanitize_csv_cell(report.report_type)])
        writer.writerow(["Period", f"{report.start_date.isoformat()} to {report.end_date.isoformat()}"])
        writer.writerow(["Currency", sanitize_csv_cell(report.currency)])
        writer.writerow([])

        # Summary section
        summary = json.loads(report.summary_metrics or "{}")
        writer.writerow(["SUMMARY METRIC", "VALUE"])
        for k, v in summary.items():
            writer.writerow([sanitize_csv_cell(k.replace('_', ' ').title()), sanitize_csv_cell(v)])
        writer.writerow([])

        # Monthly breakdown section
        details = json.loads(report.detailed_data or "{}")
        monthly = details.get("monthly_breakdown", [])
        if monthly:
            writer.writerow(["MONTHLY BREAKDOWN"])
            writer.writerow(["Period", "Income", "Expense", "Net", "Revenue", "Net Profit", "Transactions"])
            for m in monthly:
                writer.writerow([
                    sanitize_csv_cell(m.get("period")),
                    sanitize_csv_cell(m.get("income")),
                    sanitize_csv_cell(m.get("expense")),
                    sanitize_csv_cell(m.get("net")),
                    sanitize_csv_cell(m.get("revenue")),
                    sanitize_csv_cell(m.get("net_profit")),
                    sanitize_csv_cell(m.get("transaction_count"))
                ])

        csv_content = output.getvalue()
        output.close()
        filename = f"{clean_title}_{report.id[:8]}.csv"
        AuditService.log(db, current_user.id, "EXPORT_CSV", "REPORT", report.id, f"Downloaded CSV for report '{report.title}'")
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format. Use 'pdf' or 'csv'.")

@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(GeneratedReport).filter(
        GeneratedReport.id == report_id,
        GeneratedReport.user_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    db.delete(report)
    db.commit()
    AuditService.log(db, current_user.id, "DELETE", "REPORT", report_id, f"Deleted report '{report.title}'")
    return {"message": "Report deleted successfully."}
