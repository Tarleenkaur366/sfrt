from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional
import json
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.transaction import FinancialTransaction
from app.models.category import FinancialCategory
from app.models.report import GeneratedReport
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec,
    calculate_percentage_change,
    calculate_ratio
)
from app.utils.date_helpers import get_previous_period_dates

class SmartReportingEngine:
    """
    Reporting engine that converts stored database transactions into fully audit-compliant,
    structured financial reports with snapshots, methodologies, and warnings.
    """

    @staticmethod
    def generate_report(
        db: Session,
        user_id: str,
        report_type: str,
        start_date: date,
        end_date: date,
        currency: str = "INR",
        title: Optional[str] = None,
        category_ids: Optional[List[str]] = None,
        transaction_types: Optional[List[str]] = None,
        opening_cash_balance: float = 0.0,
        notes: Optional[str] = None
    ) -> GeneratedReport:
        # 1. Fetch transactions for current period
        query = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date,
            FinancialTransaction.currency == currency
        )

        if category_ids:
            query = query.filter(FinancialTransaction.category_id.in_(category_ids))
        if transaction_types:
            query = query.filter(FinancialTransaction.transaction_type.in_(transaction_types))

        transactions = query.order_by(FinancialTransaction.transaction_date.asc()).all()

        # 2. Fetch previous period transactions for comparison
        prev_start, prev_end = get_previous_period_dates(start_date, end_date)
        prev_txs = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= prev_start,
            FinancialTransaction.transaction_date <= prev_end,
            FinancialTransaction.currency == currency
        ).all()

        # 3. Calculate summary metrics for current & previous periods
        current_summary = FinancialCalculationEngine.calculate_summary(
            transactions,
            opening_cash=quantize_dec(opening_cash_balance)
        )
        prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

        # 4. Generate report-type specific data, methodology, and warnings
        data_quality_warnings = []
        methodology = ""
        detailed_data: Dict[str, Any] = {}
        summary_payload: Dict[str, Any] = {}

        if len(transactions) == 0:
            data_quality_warnings.append("No financial transactions recorded for the selected period and currency.")

        if report_type == "INCOME_EXPENSE":
            default_title = f"Income and Expense Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Total Income includes all recognized Revenue and Other Income. "
                "Total Expenses include all Operating Expenses and Cost of Goods Sold. "
                "Transfers, Asset Purchases, and Owner Contributions/Withdrawals are excluded from Operating Surplus."
            )
            income_cats = FinancialCalculationEngine.aggregate_categories(transactions, category_type_filter="INCOME")
            expense_cats = FinancialCalculationEngine.aggregate_categories(transactions, category_type_filter="EXPENSE")
            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)

            # Period comparisons
            income_change = calculate_percentage_change(current_summary["total_income"], prev_summary["total_income"])
            expense_change = calculate_percentage_change(current_summary["total_expenses"], prev_summary["total_expenses"])
            surplus_change = calculate_percentage_change(current_summary["net_surplus_deficit"], prev_summary["net_surplus_deficit"])

            summary_payload = {
                "total_income": float(current_summary["total_income"]),
                "total_expenses": float(current_summary["total_expenses"]),
                "net_surplus_deficit": float(current_summary["net_surplus_deficit"]),
                "prev_total_income": float(prev_summary["total_income"]),
                "prev_total_expenses": float(prev_summary["total_expenses"]),
                "income_growth_pct": float(income_change) if income_change is not None else None,
                "expense_growth_pct": float(expense_change) if expense_change is not None else None,
                "surplus_growth_pct": float(surplus_change) if surplus_change is not None else None,
                "transaction_count": current_summary["transaction_count"],
            }
            detailed_data = {
                "income_categories": income_cats,
                "expense_categories": expense_cats,
                "monthly_breakdown": monthly
            }

        elif report_type == "PROFIT_LOSS":
            default_title = f"Profit and Loss Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Gross Profit = Revenue − Cost of Goods Sold. "
                "Operating Profit = Gross Profit − Operating Expenses. "
                "Net Profit = Recognized Revenue & Other Income − Recognized Expenses. "
                "Assumes standard accounting classification applied during transaction entry."
            )
            if current_summary["revenue"] == Decimal("0.00"):
                data_quality_warnings.append("Zero recognized business revenue recorded; profit margins cannot be calculated.")

            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)
            rev_change = calculate_percentage_change(current_summary["revenue"], prev_summary["revenue"])
            net_profit_change = calculate_percentage_change(current_summary["net_profit"], prev_summary["net_profit"])

            summary_payload = {
                "revenue": float(current_summary["revenue"]),
                "cost_of_goods_sold": float(current_summary["cogs"]),
                "gross_profit": float(current_summary["gross_profit"]),
                "gross_profit_margin": float(current_summary["gross_profit_margin"]) if current_summary["gross_profit_margin"] is not None else None,
                "operating_expense": float(current_summary["operating_expense"]),
                "operating_profit": float(current_summary["operating_profit"]),
                "operating_profit_margin": float(current_summary["operating_profit_margin"]) if current_summary["operating_profit_margin"] is not None else None,
                "other_income": float(current_summary["other_income"]),
                "net_profit": float(current_summary["net_profit"]),
                "net_profit_margin": float(current_summary["net_profit_margin"]) if current_summary["net_profit_margin"] is not None else None,
                "revenue_growth_pct": float(rev_change) if rev_change is not None else None,
                "net_profit_growth_pct": float(net_profit_change) if net_profit_change is not None else None,
            }
            detailed_data = {
                "monthly_breakdown": monthly
            }

        elif report_type == "CASH_FLOW":
            default_title = f"Cash Flow Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Net Cash Movement = Cash Inflows − Cash Outflows. "
                "Cash inflows comprise Revenue, Other Income, and Owner Equity Contributions. "
                "Cash outflows comprise Operating Expenses, COGS, Asset Purchases, Liability Payments, and Owner Withdrawals. "
                "Internal transfers are neutral."
            )
            if opening_cash_balance == 0.0:
                data_quality_warnings.append("Opening cash balance set to 0.00; closing balance reflects net movement rather than total physical bank balance.")

            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)
            summary_payload = {
                "opening_cash_balance": float(current_summary["opening_cash"]),
                "cash_inflows": float(current_summary["cash_inflows"]),
                "cash_outflows": float(current_summary["cash_outflows"]),
                "net_cash_movement": float(current_summary["net_cash_movement"]),
                "closing_cash_balance": float(current_summary["closing_cash"]),
                "prev_cash_movement": float(prev_summary["net_cash_movement"]),
            }
            detailed_data = {
                "monthly_breakdown": monthly
            }

        elif report_type == "EXPENSE_ANALYSIS":
            default_title = f"Expense Analysis Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Detailed breakdown of Operating Expenses and Cost of Goods Sold. "
                "Categories analyzed by total outlay, percentage of overall expenses, and monthly trends."
            )
            expense_cats = FinancialCalculationEngine.aggregate_categories(transactions, category_type_filter="EXPENSE")
            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)
            exp_change = calculate_percentage_change(current_summary["total_expenses"], prev_summary["total_expenses"])

            summary_payload = {
                "total_expenses": float(current_summary["total_expenses"]),
                "prev_total_expenses": float(prev_summary["total_expenses"]),
                "expense_growth_pct": float(exp_change) if exp_change is not None else None,
                "categories_count": len(expense_cats),
                "largest_category": expense_cats[0]["category_name"] if expense_cats else "None",
                "largest_category_amount": expense_cats[0]["total_amount"] if expense_cats else 0.0,
            }
            detailed_data = {
                "categories": expense_cats,
                "monthly_breakdown": monthly
            }

        elif report_type == "REVENUE_ANALYSIS":
            default_title = f"Revenue Analysis Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Comprehensive analysis of recognized business revenue streams. "
                "Highlights top revenue generating categories and monthly growth trajectory."
            )
            revenue_cats = FinancialCalculationEngine.aggregate_categories(transactions, category_type_filter="INCOME")
            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)
            rev_change = calculate_percentage_change(current_summary["revenue"], prev_summary["revenue"])

            summary_payload = {
                "total_revenue": float(current_summary["revenue"]),
                "prev_total_revenue": float(prev_summary["revenue"]),
                "revenue_growth_pct": float(rev_change) if rev_change is not None else None,
                "categories_count": len(revenue_cats),
                "top_revenue_source": revenue_cats[0]["category_name"] if revenue_cats else "None",
            }
            detailed_data = {
                "categories": revenue_cats,
                "monthly_breakdown": monthly
            }

        elif report_type == "FINANCIAL_PERFORMANCE":
            default_title = f"Financial Performance Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = (
                "Key Performance Indicator (KPI) synthesis combining profitability, efficiency, and cash generation. "
                "Evaluates Gross Margin, Net Margin, and Expense-to-Revenue Ratio."
            )
            rev_change = calculate_percentage_change(current_summary["revenue"], prev_summary["revenue"])
            exp_change = calculate_percentage_change(current_summary["total_expenses"], prev_summary["total_expenses"])

            summary_payload = {
                "revenue": float(current_summary["revenue"]),
                "total_expenses": float(current_summary["total_expenses"]),
                "gross_profit_margin": float(current_summary["gross_profit_margin"]) if current_summary["gross_profit_margin"] is not None else None,
                "operating_profit_margin": float(current_summary["operating_profit_margin"]) if current_summary["operating_profit_margin"] is not None else None,
                "net_profit_margin": float(current_summary["net_profit_margin"]) if current_summary["net_profit_margin"] is not None else None,
                "expense_to_revenue_ratio": float(current_summary["expense_to_revenue_ratio"]) if current_summary["expense_to_revenue_ratio"] is not None else None,
                "net_cash_movement": float(current_summary["net_cash_movement"]),
                "revenue_growth_pct": float(rev_change) if rev_change is not None else None,
                "expense_growth_pct": float(exp_change) if exp_change is not None else None,
            }
            detailed_data = {
                "monthly_breakdown": FinancialCalculationEngine.aggregate_monthly(transactions)
            }

        else:  # CUSTOM
            default_title = f"Custom Financial Report ({start_date.isoformat()} to {end_date.isoformat()})"
            methodology = "Custom filtered reporting based on user-selected criteria."
            monthly = FinancialCalculationEngine.aggregate_monthly(transactions)
            categories = FinancialCalculationEngine.aggregate_categories(transactions)
            summary_payload = {
                "total_income": float(current_summary["total_income"]),
                "total_expenses": float(current_summary["total_expenses"]),
                "net_surplus_deficit": float(current_summary["net_surplus_deficit"]),
                "net_cash_movement": float(current_summary["net_cash_movement"]),
                "transaction_count": current_summary["transaction_count"],
            }
            detailed_data = {
                "categories": categories,
                "monthly_breakdown": monthly
            }

        report_title = title if title and title.strip() else default_title

        parameters_dict = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "currency": currency,
            "category_ids": category_ids,
            "transaction_types": transaction_types,
            "opening_cash_balance": opening_cash_balance,
            "methodology": methodology,
            "data_quality_warnings": data_quality_warnings
        }

        # 5. Persist the report record to database
        report = GeneratedReport(
            user_id=user_id,
            report_type=report_type,
            title=report_title,
            start_date=start_date,
            end_date=end_date,
            currency=currency,
            report_parameters=json.dumps(parameters_dict),
            summary_metrics=json.dumps(summary_payload),
            detailed_data=json.dumps(detailed_data),
            generation_status="COMPLETED",
            notes=notes
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return report
