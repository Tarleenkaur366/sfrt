from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.transaction import FinancialTransaction
from app.models.report import GeneratedReport
from app.schemas.analytics import DashboardSummaryResponse, MonthlyTrendPoint, CategoryDistributionPoint
from app.routers.deps import get_current_user
from app.routers.transactions import map_tx_response
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec,
    calculate_percentage_change
)
from app.utils.date_helpers import get_previous_period_dates

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    curr = currency.upper() if currency else current_user.default_currency or "INR"
    
    # Default date range: current year to date or last 90 days if not provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, 1, 1) if (end_date - date(end_date.year, 1, 1)).days > 30 else (end_date - timedelta(days=90))

    # Current period query
    query = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= start_date,
        FinancialTransaction.transaction_date <= end_date,
        FinancialTransaction.currency == curr
    )
    transactions = query.all()

    # Prior period query for growth comparisons
    prev_start, prev_end = get_previous_period_dates(start_date, end_date)
    prev_txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= prev_start,
        FinancialTransaction.transaction_date <= prev_end,
        FinancialTransaction.currency == curr
    ).all()

    summary = FinancialCalculationEngine.calculate_summary(transactions)
    prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

    # Calculate average monthly figures
    months_span = max(1, ((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1))
    avg_monthly_income = quantize_dec(summary["total_income"] / Decimal(months_span))
    avg_monthly_expenses = quantize_dec(summary["total_expenses"] / Decimal(months_span))

    # Revenue growth
    rev_growth = calculate_percentage_change(summary["revenue"], prev_summary["revenue"])

    # Reports generated count
    reports_count = db.query(GeneratedReport).filter(GeneratedReport.user_id == current_user.id).count()

    # Recent transactions (latest 5)
    recent_txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.currency == curr
    ).order_by(desc(FinancialTransaction.transaction_date), desc(FinancialTransaction.created_at)).limit(5).all()

    # Recent generated reports (latest 5)
    recent_reports = db.query(GeneratedReport).filter(
        GeneratedReport.user_id == current_user.id
    ).order_by(desc(GeneratedReport.created_at)).limit(5).all()

    # Alerts & badges
    alerts: List[Dict[str, Any]] = []
    if summary["total_expenses"] > summary["total_income"]:
        alerts.append({
            "type": "danger",
            "title": "Net Deficit Warning",
            "message": f"Recognized expenses exceed income by {curr} {(summary['total_expenses'] - summary['total_income']):,.2f} for this period."
        })
    if summary["transaction_count"] == 0:
        alerts.append({
            "type": "info",
            "title": "No Transactions Recorded",
            "message": "Start by adding your first transaction or importing a CSV file."
        })
    if summary["expense_to_income_ratio"] and summary["expense_to_income_ratio"] > Decimal("80.00"):
        alerts.append({
            "type": "warning",
            "title": "High Expense Ratio",
            "message": f"Expenses consume {summary['expense_to_income_ratio']:.1f}% of total income."
        })

    return {
        "currency": curr,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_income": float(summary["total_income"]),
        "total_expenses": float(summary["total_expenses"]),
        "net_surplus_deficit": float(summary["net_surplus_deficit"]),
        "net_cash_movement": float(summary["net_cash_movement"]),
        "total_transactions": summary["transaction_count"],
        "avg_monthly_income": float(avg_monthly_income),
        "avg_monthly_expenses": float(avg_monthly_expenses),
        "expense_to_income_ratio": float(summary["expense_to_income_ratio"]) if summary["expense_to_income_ratio"] is not None else None,
        "revenue_growth": float(rev_growth) if rev_growth is not None else None,
        "gross_profit": float(summary["gross_profit"]),
        "gross_profit_margin": float(summary["gross_profit_margin"]) if summary["gross_profit_margin"] is not None else None,
        "operating_profit": float(summary["operating_profit"]),
        "net_profit": float(summary["net_profit"]),
        "net_profit_margin": float(summary["net_profit_margin"]) if summary["net_profit_margin"] is not None else None,
        "reports_generated_count": reports_count,
        "recent_transactions": [map_tx_response(tx) for tx in recent_txs],
        "recent_reports": [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "created_at": r.created_at.isoformat()
            }
            for r in recent_reports
        ],
        "alerts": alerts
    }

@router.get("/income-expenses")
def get_income_expenses_chart(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    curr = currency.upper() if currency else current_user.default_currency or "INR"
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, 1, 1)

    transactions = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= start_date,
        FinancialTransaction.transaction_date <= end_date,
        FinancialTransaction.currency == curr
    ).all()

    summary = FinancialCalculationEngine.calculate_summary(transactions)
    return {
        "labels": ["Total Income", "Total Expenses", "Net Surplus/Deficit"],
        "datasets": [
            {
                "label": f"Amount ({curr})",
                "data": [
                    float(summary["total_income"]),
                    float(summary["total_expenses"]),
                    float(summary["net_surplus_deficit"])
                ],
                "backgroundColor": ["#10B981", "#EF4444", "#3B82F6"]
            }
        ]
    }

@router.get("/trends")
def get_trends_chart(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    curr = currency.upper() if currency else current_user.default_currency or "INR"
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    transactions = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= start_date,
        FinancialTransaction.transaction_date <= end_date,
        FinancialTransaction.currency == curr
    ).all()

    monthly_data = FinancialCalculationEngine.aggregate_monthly(transactions)
    return {
        "periods": [m["period"] for m in monthly_data],
        "income": [m["income"] for m in monthly_data],
        "expenses": [m["expense"] for m in monthly_data],
        "net": [m["net"] for m in monthly_data],
        "cash_inflow": [m["cash_inflow"] for m in monthly_data],
        "cash_outflow": [m["cash_outflow"] for m in monthly_data],
        "revenue": [m["revenue"] for m in monthly_data],
        "net_profit": [m["net_profit"] for m in monthly_data],
        "transaction_count": [m["transaction_count"] for m in monthly_data]
    }

@router.get("/category-distribution")
def get_category_distribution_chart(
    category_type: str = Query("EXPENSE"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    currency: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    curr = currency.upper() if currency else current_user.default_currency or "INR"
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = date(end_date.year, 1, 1)

    transactions = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_id == current_user.id,
        FinancialTransaction.transaction_date >= start_date,
        FinancialTransaction.transaction_date <= end_date,
        FinancialTransaction.currency == curr
    ).all()

    categories = FinancialCalculationEngine.aggregate_categories(
        transactions,
        category_type_filter=category_type
    )

    labels = [c["category_name"] for c in categories[:10]]
    values = [c["total_amount"] for c in categories[:10]]
    percentages = [c["percentage"] for c in categories[:10]]

    return {
        "labels": labels,
        "values": values,
        "percentages": percentages,
        "category_type": category_type,
        "currency": curr
    }
