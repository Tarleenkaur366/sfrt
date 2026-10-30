import io
import csv
from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.database import get_db
from app.models.user import User
from app.models.transaction import FinancialTransaction
from app.models.category import FinancialCategory
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    VALID_TRANSACTION_TYPES
)
from app.routers.deps import get_current_user
from app.services.calculation_engine import quantize_dec
from app.services.audit_service import AuditService
from app.utils.csv_sanitizer import sanitize_csv_cell

router = APIRouter(prefix="/transactions", tags=["Transactions"])

def map_tx_response(tx: FinancialTransaction) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        user_id=tx.user_id,
        category_id=tx.category_id,
        category_name=tx.category.name if tx.category else "Uncategorized",
        category_type=tx.category.category_type if tx.category else None,
        transaction_date=tx.transaction_date,
        description=tx.description,
        transaction_type=tx.transaction_type,
        amount=quantize_dec(tx.amount),
        currency=tx.currency,
        payment_method=tx.payment_method,
        reference_number=tx.reference_number,
        notes=tx.notes,
        is_sample=tx.is_sample,
        created_at=tx.created_at,
        updated_at=tx.updated_at
    )

@router.get("", response_model=TransactionListResponse)
def list_transactions(
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: str = Query("transaction_date"),
    sort_dir: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialTransaction).filter(FinancialTransaction.user_id == current_user.id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                FinancialTransaction.description.ilike(term),
                FinancialTransaction.reference_number.ilike(term),
                FinancialTransaction.notes.ilike(term)
            )
        )

    if start_date:
        query = query.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(FinancialTransaction.transaction_date <= end_date)
    if category_id:
        query = query.filter(FinancialTransaction.category_id == category_id)
    if transaction_type:
        query = query.filter(FinancialTransaction.transaction_type == transaction_type)
    if currency:
        query = query.filter(FinancialTransaction.currency == currency.upper())

    total = query.count()

    # Sorting
    sort_col = getattr(FinancialTransaction, sort_by, FinancialTransaction.transaction_date)
    if sort_dir.lower() == "asc":
        query = query.order_by(asc(sort_col), asc(FinancialTransaction.id))
    else:
        query = query.order_by(desc(sort_col), desc(FinancialTransaction.id))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return TransactionListResponse(
        items=[map_tx_response(tx) for tx in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/export/csv")
def export_transactions_csv(
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialTransaction).filter(FinancialTransaction.user_id == current_user.id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                FinancialTransaction.description.ilike(term),
                FinancialTransaction.reference_number.ilike(term)
            )
        )
    if start_date:
        query = query.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(FinancialTransaction.transaction_date <= end_date)
    if category_id:
        query = query.filter(FinancialTransaction.category_id == category_id)
    if transaction_type:
        query = query.filter(FinancialTransaction.transaction_type == transaction_type)
    if currency:
        query = query.filter(FinancialTransaction.currency == currency.upper())

    transactions = query.order_by(desc(FinancialTransaction.transaction_date)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Transaction ID",
        "Date",
        "Description",
        "Transaction Type",
        "Category",
        "Amount",
        "Currency",
        "Payment Method",
        "Reference Number",
        "Notes",
        "Is Sample"
    ])

    for tx in transactions:
        cat_name = tx.category.name if tx.category else "Uncategorized"
        writer.writerow([
            sanitize_csv_cell(tx.id),
            sanitize_csv_cell(tx.transaction_date.isoformat()),
            sanitize_csv_cell(tx.description),
            sanitize_csv_cell(tx.transaction_type),
            sanitize_csv_cell(cat_name),
            sanitize_csv_cell(f"{quantize_dec(tx.amount):.2f}"),
            sanitize_csv_cell(tx.currency),
            sanitize_csv_cell(tx.payment_method or ""),
            sanitize_csv_cell(tx.reference_number or ""),
            sanitize_csv_cell(tx.notes or ""),
            "Yes" if tx.is_sample else "No"
        ])

    csv_data = output.getvalue()
    output.close()

    AuditService.log(db, current_user.id, "EXPORT", "TRANSACTION", None, f"Exported {len(transactions)} transactions to CSV")

    filename = f"transactions_{date.today().isoformat()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    req: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify category if given
    category = None
    if req.category_id:
        category = db.query(FinancialCategory).filter(
            FinancialCategory.id == req.category_id,
            FinancialCategory.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected category does not exist.")

    tx = FinancialTransaction(
        user_id=current_user.id,
        category_id=req.category_id,
        transaction_date=req.transaction_date,
        description=req.description.strip(),
        transaction_type=req.transaction_type,
        amount=quantize_dec(req.amount),
        currency=req.currency.upper(),
        payment_method=req.payment_method,
        reference_number=req.reference_number.strip() if req.reference_number else None,
        notes=req.notes.strip() if req.notes else None,
        is_sample=req.is_sample
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    AuditService.log(db, current_user.id, "CREATE", "TRANSACTION", tx.id, f"Added transaction '{tx.description}' for {tx.currency} {tx.amount}")
    return map_tx_response(tx)

@router.get("/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    tx_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(FinancialTransaction).filter(
        FinancialTransaction.id == tx_id,
        FinancialTransaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return map_tx_response(tx)

@router.patch("/{tx_id}", response_model=TransactionResponse)
def update_transaction(
    tx_id: str,
    req: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(FinancialTransaction).filter(
        FinancialTransaction.id == tx_id,
        FinancialTransaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    if req.category_id is not None:
        if req.category_id != "":
            cat = db.query(FinancialCategory).filter(
                FinancialCategory.id == req.category_id,
                FinancialCategory.user_id == current_user.id
            ).first()
            if not cat:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected category does not exist.")
            tx.category_id = req.category_id
        else:
            tx.category_id = None

    if req.transaction_date is not None:
        tx.transaction_date = req.transaction_date
    if req.description is not None:
        tx.description = req.description.strip()
    if req.transaction_type is not None:
        tx.transaction_type = req.transaction_type
    if req.amount is not None:
        tx.amount = quantize_dec(req.amount)
    if req.currency is not None:
        tx.currency = req.currency.upper()
    if req.payment_method is not None:
        tx.payment_method = req.payment_method
    if req.reference_number is not None:
        tx.reference_number = req.reference_number.strip() if req.reference_number else None
    if req.notes is not None:
        tx.notes = req.notes.strip() if req.notes else None

    db.commit()
    db.refresh(tx)
    AuditService.log(db, current_user.id, "UPDATE", "TRANSACTION", tx.id, f"Updated transaction '{tx.description}'")
    return map_tx_response(tx)

@router.delete("/{tx_id}")
def delete_transaction(
    tx_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(FinancialTransaction).filter(
        FinancialTransaction.id == tx_id,
        FinancialTransaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    desc = tx.description
    db.delete(tx)
    db.commit()
    AuditService.log(db, current_user.id, "DELETE", "TRANSACTION", tx_id, f"Deleted transaction '{desc}'")
    return {"message": "Transaction deleted successfully."}
