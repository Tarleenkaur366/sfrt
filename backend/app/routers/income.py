from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    TransactionListResponse
)
from app.routers.transactions import map_tx_response
from app.routers.deps import get_current_user
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/income", tags=["Income Management"])

INCOME_TYPES = ["Revenue", "Other Income"]

@router.get("", response_model=TransactionListResponse)
def list_income(
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_type.in_(INCOME_TYPES)
    )

    if search and search.strip():
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
    if currency:
        query = query.filter(FinancialTransaction.currency == currency.upper())

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(FinancialTransaction.transaction_date)).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return TransactionListResponse(
        items=[map_tx_response(tx) for tx in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/summary")
def get_income_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: str = Query("INR"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.currency == currency.upper(),
        FinancialTransaction.transaction_type.in_(INCOME_TYPES)
    )
    if start_date:
        query = query.filter(FinancialTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(FinancialTransaction.transaction_date <= end_date)

    txs = query.all()
    total_income = sum((quantize_dec(tx.amount) for tx in txs), quantize_dec(0))
    categories = FinancialCalculationEngine.aggregate_categories(txs, category_type_filter="INCOME")

    return {
        "currency": currency.upper(),
        "total_income": float(total_income),
        "transaction_count": len(txs),
        "categories": categories
    }

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    req: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.transaction_type not in INCOME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Income transaction type must be one of: {', '.join(INCOME_TYPES)}"
        )

    if req.category_id:
        cat = db.query(FinancialCategory).filter(
            FinancialCategory.id == req.category_id,
            FinancialCategory.user_id == current_user.id
        ).first()
        if not cat:
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
    AuditService.log(db, current_user.id, "CREATE", "INCOME", tx.id, f"Added income '{tx.description}' for {tx.currency} {tx.amount}")
    return map_tx_response(tx)

@router.patch("/{tx_id}", response_model=TransactionResponse)
def update_income(
    tx_id: str,
    req: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(FinancialTransaction).filter(
        FinancialTransaction.id == tx_id,
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_type.in_(INCOME_TYPES)
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income record not found.")

    if req.transaction_type and req.transaction_type not in INCOME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Income transaction type must be one of: {', '.join(INCOME_TYPES)}"
        )

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
    return map_tx_response(tx)

@router.delete("/{tx_id}")
def delete_income(
    tx_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(FinancialTransaction).filter(
        FinancialTransaction.id == tx_id,
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_type.in_(INCOME_TYPES)
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income record not found.")

    db.delete(tx)
    db.commit()
    AuditService.log(db, current_user.id, "DELETE", "INCOME", tx_id, "Deleted income record")
    return {"message": "Income record deleted successfully."}
