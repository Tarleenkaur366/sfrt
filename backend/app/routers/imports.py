import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.import_job import ImportJob
from app.schemas.import_job import (
    ImportPreviewResponse,
    ImportConfirmRequest,
    ImportJobResponse
)
from app.routers.deps import get_current_user
from app.services.import_service import ImportService
from app.services.audit_service import AuditService
from app.config import settings

router = APIRouter(prefix="/imports", tags=["CSV Import"])

@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_csv_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files (.csv) are supported."
        )

    content = await file.read()
    if len(content) > settings.MAX_CSV_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_CSV_SIZE_BYTES // (1024*1024)}MB."
        )

    try:
        preview = ImportService.preview_csv(
            db=db,
            user_id=current_user.id,
            file_content=content,
            file_name=file.filename
        )
        return preview
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process CSV: {str(e)}")

@router.post("/confirm", response_model=ImportJobResponse)
def confirm_csv_import(
    req: ImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.records:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No records provided for import.")

    try:
        job = ImportService.commit_import(
            db=db,
            user_id=current_user.id,
            file_name=req.file_name,
            records=req.records,
            skip_duplicates=req.skip_duplicates
        )
        AuditService.log(
            db,
            current_user.id,
            "IMPORT",
            "TRANSACTION",
            job.id,
            f"Imported {job.successful_rows} transactions from {req.file_name}"
        )
        return ImportJobResponse(
            id=job.id,
            user_id=job.user_id,
            file_name=job.file_name,
            import_type=job.import_type,
            status=job.status,
            total_rows=job.total_rows,
            successful_rows=job.successful_rows,
            failed_rows=job.failed_rows,
            duplicate_rows=job.duplicate_rows,
            error_summary=json.loads(job.error_summary) if job.error_summary and job.error_summary.startswith("[") else None,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Import failed: {str(e)}")

@router.get("", response_model=List[ImportJobResponse])
def list_import_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jobs = db.query(ImportJob).filter(
        ImportJob.user_id == current_user.id
    ).order_by(desc(ImportJob.created_at)).all()

    return [
        ImportJobResponse(
            id=j.id,
            user_id=j.user_id,
            file_name=j.file_name,
            import_type=j.import_type,
            status=j.status,
            total_rows=j.total_rows,
            successful_rows=j.successful_rows,
            failed_rows=j.failed_rows,
            duplicate_rows=j.duplicate_rows,
            error_summary=json.loads(j.error_summary) if j.error_summary and j.error_summary.startswith("[") else None,
            created_at=j.created_at,
            completed_at=j.completed_at
        )
        for j in jobs
    ]

@router.get("/sample-csv")
def download_sample_csv():
    sample_content = (
        "transaction_date,description,transaction_type,category,amount,currency,payment_method,reference_number,notes\n"
        "2026-01-15,Client Consulting Contract,Revenue,Service Revenue,85000.00,INR,Bank Transfer,INV-2026-001,Monthly retainer\n"
        "2026-01-18,Commercial Office Rent,Operating Expense,Rent,30000.00,INR,Bank Transfer,RENT-JAN-26,HQ rent\n"
        "2026-01-20,Product Sales E-Commerce,Revenue,Sales Revenue,42500.00,INR,UPI,ORD-7819,Online store sales\n"
        "2026-01-22,Team Salaries,Operating Expense,Salaries,45000.00,INR,Bank Transfer,PAY-2026-01,Core team wages\n"
        "2026-01-25,Software Subscriptions,Operating Expense,Software,4200.00,INR,Credit Card,SUB-9021,Cloud services\n"
        "2026-01-28,Raw Material Purchase,Cost of Goods Sold,Inventory,18000.00,INR,Bank Transfer,PO-4412,Production inventory\n"
    )
    return Response(
        content=sample_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_financial_transactions.csv"}
    )
