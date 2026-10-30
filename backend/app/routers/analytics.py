from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.transaction import FinancialTransaction
from app.routers.deps import get_current_user
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec,
    calculate_percentage_change
)
from app.utils.date_helpers import get_previous_period_dates

router = APIRouter(prefix="/analytics", tags=["Analytics"])

def get_analytics_dates(start_date: Optional[date], end_date: Optional[date]):
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, 1, 1)
    return start_date, end_date

@router.get("/revenue")
def get_revenue_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s_date, e_date = get_analytics_dates(start_date, end_date)
    curr = currency.upper() if currency else current_user.default_currency or "INR"

    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= s_date,
        FinancialTransaction.transaction_date <= e_date,
        FinancialTransaction.currency == curr
    ).all()

    prev_s, prev_e = get_previous_period_dates(s_date, e_date)
    prev_txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= prev_s,
        FinancialTransaction.transaction_date <= prev_e,
        FinancialTransaction.currency == curr
    ).all()

    curr_summary = FinancialCalculationEngine.calculate_summary(txs)
    prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

    growth = calculate_percentage_change(curr_summary["revenue"], prev_summary["revenue"])
    monthly = FinancialCalculationEngine.aggregate_monthly(txs)
    cats = FinancialCalculationEngine.aggregate_categories(txs, category_type_filter="INCOME")

    return {
        "currency": curr,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "total_revenue": float(curr_summary["revenue"]),
        "previous_period_revenue": float(prev_summary["revenue"]),
        "revenue_growth_pct": float(growth) if growth is not None else None,
        "monthly_trends": monthly,
        "category_breakdown": cats
    }

@router.get("/expenses")
def get_expense_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s_date, e_date = get_analytics_dates(start_date, end_date)
    curr = currency.upper() if currency else current_user.default_currency or "INR"

    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= s_date,
        FinancialTransaction.transaction_date <= e_date,
        FinancialTransaction.currency == curr
    ).all()

    prev_s, prev_e = get_previous_period_dates(s_date, e_date)
    prev_txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= prev_s,
        FinancialTransaction.transaction_date <= prev_e,
        FinancialTransaction.currency == curr
    ).all()

    curr_summary = FinancialCalculationEngine.calculate_summary(txs)
    prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

    growth = calculate_percentage_change(curr_summary["total_expenses"], prev_summary["total_expenses"])
    monthly = FinancialCalculationEngine.aggregate_monthly(txs)
    cats = FinancialCalculationEngine.aggregate_categories(txs, category_type_filter="EXPENSE")

    return {
        "currency": curr,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "total_expenses": float(curr_summary["total_expenses"]),
        "previous_period_expenses": float(prev_summary["total_expenses"]),
        "expense_growth_pct": float(growth) if growth is not None else None,
        "monthly_trends": monthly,
        "category_breakdown": cats,
        "largest_categories": cats[:5]
    }

@router.get("/cash-flow")
def get_cash_flow_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    opening_balance: float = Query(0.0),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s_date, e_date = get_analytics_dates(start_date, end_date)
    curr = currency.upper() if currency else current_user.default_currency or "INR"

    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= s_date,
        FinancialTransaction.transaction_date <= e_date,
        FinancialTransaction.currency == curr
    ).all()

    summary = FinancialCalculationEngine.calculate_summary(txs, opening_cash=quantize_dec(opening_balance))
    monthly = FinancialCalculationEngine.aggregate_monthly(txs)

    return {
        "currency": curr,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "opening_balance": float(summary["opening_cash"]),
        "total_inflows": float(summary["cash_inflows"]),
        "total_outflows": float(summary["cash_outflows"]),
        "net_cash_movement": float(summary["net_cash_movement"]),
        "estimated_closing_balance": float(summary["closing_cash"]),
        "monthly_trends": monthly
    }

@router.get("/profit-loss")
def get_profit_loss_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s_date, e_date = get_analytics_dates(start_date, end_date)
    curr = currency.upper() if currency else current_user.default_currency or "INR"

    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= s_date,
        FinancialTransaction.transaction_date <= e_date,
        FinancialTransaction.currency == curr
    ).all()

    summary = FinancialCalculationEngine.calculate_summary(txs)
    monthly = FinancialCalculationEngine.aggregate_monthly(txs)

    return {
        "currency": curr,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "revenue": float(summary["revenue"]),
        "cost_of_goods_sold": float(summary["cogs"]),
        "gross_profit": float(summary["gross_profit"]),
        "gross_profit_margin_pct": float(summary["gross_profit_margin"]) if summary["gross_profit_margin"] is not None else None,
        "operating_expenses": float(summary["operating_expense"]),
        "operating_profit": float(summary["operating_profit"]),
        "operating_profit_margin_pct": float(summary["operating_profit_margin"]) if summary["operating_profit_margin"] is not None else None,
        "other_income": float(summary["other_income"]),
        "net_profit": float(summary["net_profit"]),
        "net_profit_margin_pct": float(summary["net_profit_margin"]) if summary["net_profit_margin"] is not None else None,
        "monthly_trends": monthly
    }

@router.get("/financial-performance")
def get_financial_performance_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s_date, e_date = get_analytics_dates(start_date, end_date)
    curr = currency.upper() if currency else current_user.default_currency or "INR"

    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= s_date,
        FinancialTransaction.transaction_date <= e_date,
        FinancialTransaction.currency == curr
    ).all()

    prev_s, prev_e = get_previous_period_dates(s_date, e_date)
    prev_txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= prev_s,
        FinancialTransaction.transaction_date <= prev_e,
        FinancialTransaction.currency == curr
    ).all()

    curr_summary = FinancialCalculationEngine.calculate_summary(txs)
    prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

    rev_growth = calculate_percentage_change(curr_summary["revenue"], prev_summary["revenue"])
    exp_growth = calculate_percentage_change(curr_summary["total_expenses"], prev_summary["total_expenses"])

    return {
        "currency": curr,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "gross_profit_margin": float(curr_summary["gross_profit_margin"]) if curr_summary["gross_profit_margin"] is not None else None,
        "operating_profit_margin": float(curr_summary["operating_profit_margin"]) if curr_summary["operating_profit_margin"] is not None else None,
        "net_profit_margin": float(curr_summary["net_profit_margin"]) if curr_summary["net_profit_margin"] is not None else None,
        "expense_to_revenue_ratio": float(curr_summary["expense_to_revenue_ratio"]) if curr_summary["expense_to_revenue_ratio"] is not None else None,
        "revenue_growth": float(rev_growth) if rev_growth is not None else None,
        "expense_growth": float(exp_growth) if exp_growth is not None else None,
        "net_cash_movement": float(curr_summary["net_cash_movement"]),
        "monthly_trends": FinancialCalculationEngine.aggregate_monthly(txs)
    }
