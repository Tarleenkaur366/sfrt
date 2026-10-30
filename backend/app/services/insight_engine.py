from decimal import Decimal
from typing import List, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from app.models.transaction import FinancialTransaction
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec,
    calculate_percentage_change,
    calculate_ratio
)
from app.utils.date_helpers import get_previous_period_dates

class SmartInsightEngine:
    """
    Transparent, deterministic rule-based financial insight engine.
    Derives factual observations directly from database transactions.
    """

    @staticmethod
    def generate_insights(
        db: Session,
        user_id: str,
        start_date: date,
        end_date: date,
        currency: str = "INR"
    ) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        period_str = f"{start_date.isoformat()} to {end_date.isoformat()}"

        # Current period data
        current_txs = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= start_date,
            FinancialTransaction.transaction_date <= end_date,
            FinancialTransaction.currency == currency
        ).all()

        if not current_txs:
            insights.append({
                "id": "ins-empty-data",
                "title": "No Financial Records Found",
                "description": "No financial transactions were recorded for the selected date range.",
                "metric_name": "Transaction Count",
                "metric_value": "0",
                "period": period_str,
                "calculation_explanation": "Count of transactions in database between start_date and end_date equals 0.",
                "severity": "info",
                "category": "data_quality"
            })
            return insights

        # Previous period data
        prev_start, prev_end = get_previous_period_dates(start_date, end_date)
        prev_txs = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= prev_start,
            FinancialTransaction.transaction_date <= prev_end,
            FinancialTransaction.currency == currency
        ).all()

        curr_summary = FinancialCalculationEngine.calculate_summary(current_txs)
        prev_summary = FinancialCalculationEngine.calculate_summary(prev_txs)

        # 1. Net Deficit Alert
        if curr_summary["total_expenses"] > curr_summary["total_income"]:
            deficit = curr_summary["total_expenses"] - curr_summary["total_income"]
            insights.append({
                "id": "ins-net-deficit",
                "title": "Operating Outflows Exceed Inflows",
                "description": f"Recognized expenses exceed total income by {currency} {deficit:,.2f} for the selected period.",
                "metric_name": "Net Deficit",
                "metric_value": f"{currency} {deficit:,.2f}",
                "period": period_str,
                "calculation_explanation": f"Total Expenses ({currency} {curr_summary['total_expenses']:,.2f}) − Total Income ({currency} {curr_summary['total_income']:,.2f}) = Deficit of {currency} {deficit:,.2f}.",
                "severity": "danger",
                "category": "profitability"
            })
        elif curr_summary["total_income"] > Decimal("0.00") and curr_summary["net_surplus_deficit"] > Decimal("0.00"):
            insights.append({
                "id": "ins-net-surplus",
                "title": "Positive Operating Cash Surplus",
                "description": f"The organization generated a net surplus of {currency} {curr_summary['net_surplus_deficit']:,.2f}.",
                "metric_name": "Net Surplus",
                "metric_value": f"{currency} {curr_summary['net_surplus_deficit']:,.2f}",
                "period": period_str,
                "calculation_explanation": f"Total Income ({currency} {curr_summary['total_income']:,.2f}) − Total Expenses ({currency} {curr_summary['total_expenses']:,.2f}).",
                "severity": "success",
                "category": "profitability"
            })

        # 2. Period-over-Period Expense Growth Comparison
        if prev_summary["total_expenses"] > Decimal("0.00"):
            exp_change_pct = calculate_percentage_change(curr_summary["total_expenses"], prev_summary["total_expenses"])
            if exp_change_pct is not None and exp_change_pct > Decimal("10.00"):
                diff = curr_summary["total_expenses"] - prev_summary["total_expenses"]
                insights.append({
                    "id": "ins-expense-growth",
                    "title": "Expenses Increased Compared with Previous Period",
                    "description": f"Total recognized expenses grew by {exp_change_pct:.1f}% (+{currency} {diff:,.2f}) compared to the preceding period.",
                    "metric_name": "Expense Growth Rate",
                    "metric_value": f"+{exp_change_pct:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"(Current Expenses ({curr_summary['total_expenses']}) − Previous Expenses ({prev_summary['total_expenses']})) / Previous Expenses * 100.",
                    "severity": "warning",
                    "category": "expense"
                })
            elif exp_change_pct is not None and exp_change_pct < Decimal("-10.00"):
                insights.append({
                    "id": "ins-expense-decrease",
                    "title": "Expense Reductions Achieved",
                    "description": f"Total expenses declined by {abs(exp_change_pct):.1f}% relative to the preceding period.",
                    "metric_name": "Expense Reduction Rate",
                    "metric_value": f"{exp_change_pct:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"(Current Expenses − Previous Expenses) / Previous Expenses * 100.",
                    "severity": "success",
                    "category": "expense"
                })
        else:
            insights.append({
                "id": "ins-insufficient-history",
                "title": "More Historical Records Needed for Period Comparisons",
                "description": f"Prior comparison period ({prev_start.isoformat()} to {prev_end.isoformat()}) has zero recorded expenses.",
                "metric_name": "Historical Data Availability",
                "metric_value": "0 transactions in prior period",
                "period": period_str,
                "calculation_explanation": "Percentage change calculation requires a non-zero previous value in the denominator.",
                "severity": "info",
                "category": "data_quality"
            })

        # 3. Revenue Comparison
        if prev_summary["revenue"] > Decimal("0.00"):
            rev_change_pct = calculate_percentage_change(curr_summary["revenue"], prev_summary["revenue"])
            if rev_change_pct is not None and rev_change_pct < Decimal("-5.00"):
                rev_diff = prev_summary["revenue"] - curr_summary["revenue"]
                insights.append({
                    "id": "ins-revenue-contraction",
                    "title": "Revenue Decreased Relative to Previous Period",
                    "description": f"Recognized revenue contracted by {abs(rev_change_pct):.1f}% (−{currency} {rev_diff:,.2f}) from the preceding period.",
                    "metric_name": "Revenue Change",
                    "metric_value": f"{rev_change_pct:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"(Current Revenue − Previous Revenue) / Previous Revenue * 100.",
                    "severity": "warning",
                    "category": "revenue"
                })
            elif rev_change_pct is not None and rev_change_pct > Decimal("10.00"):
                insights.append({
                    "id": "ins-revenue-growth",
                    "title": "Robust Revenue Expansion",
                    "description": f"Recognized revenue grew by {rev_change_pct:.1f}% over the previous period.",
                    "metric_name": "Revenue Growth Rate",
                    "metric_value": f"+{rev_change_pct:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"(Current Revenue − Previous Revenue) / Previous Revenue * 100.",
                    "severity": "success",
                    "category": "revenue"
                })

        # 4. Dominant Expense Concentration Analysis
        expense_cats = FinancialCalculationEngine.aggregate_categories(current_txs, category_type_filter="EXPENSE")
        if expense_cats and curr_summary["total_expenses"] > Decimal("0.00"):
            top_cat = expense_cats[0]
            top_pct = Decimal(str(top_cat["percentage"]))
            if top_pct >= Decimal("30.00"):
                insights.append({
                    "id": "ins-dominant-expense",
                    "title": f"'{top_cat['category_name']}' Represents a Significant Share of Expenses",
                    "description": f"{top_cat['category_name']} accounts for {top_pct:.1f}% ({currency} {top_cat['total_amount']:,.2f}) of all recorded expenses.",
                    "metric_name": "Category Concentration",
                    "metric_value": f"{top_pct:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"({top_cat['category_name']} Total / Total Expenses) * 100.",
                    "severity": "warning" if top_pct > Decimal("45.00") else "info",
                    "category": "expense"
                })

        # 5. Expense-to-Income / Revenue Efficiency
        if curr_summary["expense_to_income_ratio"] is not None:
            ratio = curr_summary["expense_to_income_ratio"]
            if ratio >= Decimal("85.00"):
                insights.append({
                    "id": "ins-high-expense-ratio",
                    "title": "High Outflow-to-Inflow Ratio",
                    "description": f"Expenses consume {ratio:.1f}% of total recognized income, leaving minimal cash buffer.",
                    "metric_name": "Expense-to-Income Ratio",
                    "metric_value": f"{ratio:.1f}%",
                    "period": period_str,
                    "calculation_explanation": f"(Total Expenses ({curr_summary['total_expenses']}) / Total Income ({curr_summary['total_income']})) * 100.",
                    "severity": "warning",
                    "category": "profitability"
                })

        # 6. Cash Flow & Opening Balance Notice
        insights.append({
            "id": "ins-cash-flow-notice",
            "title": "Cash Movement Tracking Notice",
            "description": "Calculations represent recorded net inflows and outflows during the period. Formal bank reconciliation requires verified opening and closing bank statement balances.",
            "metric_name": "Net Cash Movement",
            "metric_value": f"{currency} {curr_summary['net_cash_movement']:,.2f}",
            "period": period_str,
            "calculation_explanation": "Cash Inflows − Cash Outflows across recorded transactions.",
            "severity": "info",
            "category": "cash_flow"
        })

        return insights
