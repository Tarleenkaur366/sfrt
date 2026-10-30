from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, List
import pandas as pd

TWO_PLACES = Decimal("0.01")

def quantize_dec(val: Any) -> Decimal:
    """Safely converts and quantizes any numeric to Decimal with 2 decimal places."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")

def calculate_percentage_change(current: Decimal, previous: Decimal) -> Optional[Decimal]:
    """
    Calculates percentage change:
    ((Current - Previous) / |Previous|) * 100
    Only calculated when previous is nonzero. Returns None if previous == 0.
    """
    if previous == Decimal("0.00") or previous is None:
        return None
    abs_prev = abs(previous)
    change = ((current - previous) / abs_prev) * Decimal("100.00")
    return quantize_dec(change)

def calculate_ratio(numerator: Decimal, denominator: Decimal) -> Optional[Decimal]:
    """
    Calculates percentage ratio: (numerator / denominator) * 100.
    Returns None if denominator <= 0 to prevent division by zero or invalid negative ratios.
    """
    if denominator is None or denominator <= Decimal("0.00"):
        return None
    ratio = (numerator / denominator) * Decimal("100.00")
    return quantize_dec(ratio)

class FinancialCalculationEngine:
    """
    Dedicated Python calculation engine implementing robust accounting arithmetic
    using Python Decimal.
    """

    @staticmethod
    def classify_totals(transactions: List[Any]) -> Dict[str, Decimal]:
        """
        Classifies and aggregates transactions strictly by their financial type:
        - Revenue
        - Other Income
        - Operating Expense
        - Cost of Goods Sold
        - Asset Purchase
        - Liability Payment
        - Owner Contribution
        - Owner Withdrawal
        - Transfer
        """
        totals: Dict[str, Decimal] = {
            "Revenue": Decimal("0.00"),
            "Other Income": Decimal("0.00"),
            "Operating Expense": Decimal("0.00"),
            "Cost of Goods Sold": Decimal("0.00"),
            "Asset Purchase": Decimal("0.00"),
            "Liability Payment": Decimal("0.00"),
            "Owner Contribution": Decimal("0.00"),
            "Owner Withdrawal": Decimal("0.00"),
            "Transfer": Decimal("0.00"),
        }

        for tx in transactions:
            t_type = getattr(tx, "transaction_type", "")
            amt = quantize_dec(getattr(tx, "amount", 0))
            if t_type in totals:
                totals[t_type] += amt

        return totals

    @staticmethod
    def calculate_summary(transactions: List[Any], opening_cash: Decimal = Decimal("0.00")) -> Dict[str, Any]:
        """
        Computes all standard financial metrics from raw transaction records.
        """
        totals = FinancialCalculationEngine.classify_totals(transactions)
        
        # Recognized Income = Revenue + Other Income
        total_income = totals["Revenue"] + totals["Other Income"]
        
        # Recognized Expenses = Operating Expense + Cost of Goods Sold
        total_expenses = totals["Operating Expense"] + totals["Cost of Goods Sold"]
        
        # Net Surplus or Deficit (Cash/Operating surplus - distinct from formal profit)
        net_surplus_deficit = total_income - total_expenses
        
        # Gross Profit = Revenue - Cost of Goods Sold
        gross_profit = totals["Revenue"] - totals["Cost of Goods Sold"]
        
        # Operating Profit = Gross Profit - Operating Expenses
        operating_profit = gross_profit - totals["Operating Expense"]
        
        # Net Profit = (Revenue + Other Income) - (Cost of Goods Sold + Operating Expense)
        # Note: If no non-operating items, equals operating_profit + other_income
        net_profit = (totals["Revenue"] + totals["Other Income"]) - (totals["Cost of Goods Sold"] + totals["Operating Expense"])
        
        # Profit Margins (calculated only when Revenue > 0)
        revenue = totals["Revenue"]
        gross_profit_margin = calculate_ratio(gross_profit, revenue)
        operating_profit_margin = calculate_ratio(operating_profit, revenue)
        net_profit_margin = calculate_ratio(net_profit, revenue)
        
        # Expense to Income & Expense to Revenue ratios
        expense_to_income_ratio = calculate_ratio(total_expenses, total_income)
        expense_to_revenue_ratio = calculate_ratio(total_expenses, revenue)
        
        # Cash Flow Calculations:
        # Cash Inflows: Revenue, Other Income, Owner Contribution
        # (Transfers are net-neutral and not treated as external inflow/outflow)
        cash_inflows = totals["Revenue"] + totals["Other Income"] + totals["Owner Contribution"]
        
        # Cash Outflows: Operating Expense, COGS, Asset Purchase, Liability Payment, Owner Withdrawal
        cash_outflows = (
            totals["Operating Expense"] +
            totals["Cost of Goods Sold"] +
            totals["Asset Purchase"] +
            totals["Liability Payment"] +
            totals["Owner Withdrawal"]
        )
        
        net_cash_movement = cash_inflows - cash_outflows
        closing_cash_balance = opening_cash + net_cash_movement

        return {
            "totals_by_type": totals,
            "total_income": quantize_dec(total_income),
            "total_expenses": quantize_dec(total_expenses),
            "net_surplus_deficit": quantize_dec(net_surplus_deficit),
            "revenue": quantize_dec(revenue),
            "cogs": quantize_dec(totals["Cost of Goods Sold"]),
            "gross_profit": quantize_dec(gross_profit),
            "gross_profit_margin": gross_profit_margin,
            "operating_expense": quantize_dec(totals["Operating Expense"]),
            "operating_profit": quantize_dec(operating_profit),
            "operating_profit_margin": operating_profit_margin,
            "other_income": quantize_dec(totals["Other Income"]),
            "net_profit": quantize_dec(net_profit),
            "net_profit_margin": net_profit_margin,
            "expense_to_income_ratio": expense_to_income_ratio,
            "expense_to_revenue_ratio": expense_to_revenue_ratio,
            "cash_inflows": quantize_dec(cash_inflows),
            "cash_outflows": quantize_dec(cash_outflows),
            "net_cash_movement": quantize_dec(net_cash_movement),
            "opening_cash": quantize_dec(opening_cash),
            "closing_cash": quantize_dec(closing_cash_balance),
            "transaction_count": len(transactions),
        }

    @staticmethod
    def aggregate_monthly(transactions: List[Any]) -> List[Dict[str, Any]]:
        """
        Uses pandas for grouping transactions by month and calculating totals.
        """
        if not transactions:
            return []

        rows = []
        for tx in transactions:
            t_date = getattr(tx, "transaction_date")
            rows.append({
                "date": pd.to_datetime(t_date),
                "type": getattr(tx, "transaction_type", ""),
                "amount": float(getattr(tx, "amount", 0)),
                "id": getattr(tx, "id", "")
            })

        df = pd.DataFrame(rows)
        df["month"] = df["date"].dt.strftime("%Y-%m")

        grouped = df.groupby(["month", "type"])["amount"].sum().unstack(fill_value=0.0)
        
        # Ensure all types exist in columns
        for col in [
            "Revenue", "Other Income", "Operating Expense", "Cost of Goods Sold",
            "Asset Purchase", "Liability Payment", "Owner Contribution", "Owner Withdrawal", "Transfer"
        ]:
            if col not in grouped.columns:
                grouped[col] = 0.0

        results = []
        for month_str, row in grouped.sort_index().iterrows():
            rev = quantize_dec(row["Revenue"])
            oth_inc = quantize_dec(row["Other Income"])
            op_exp = quantize_dec(row["Operating Expense"])
            cogs = quantize_dec(row["Cost of Goods Sold"])
            ast_pur = quantize_dec(row["Asset Purchase"])
            lia_pay = quantize_dec(row["Liability Payment"])
            own_con = quantize_dec(row["Owner Contribution"])
            own_wth = quantize_dec(row["Owner Withdrawal"])

            tot_inc = rev + oth_inc
            tot_exp = op_exp + cogs
            net = tot_inc - tot_exp
            gross_p = rev - cogs
            net_p = (rev + oth_inc) - (op_exp + cogs)
            inflow = rev + oth_inc + own_con
            outflow = op_exp + cogs + ast_pur + lia_pay + own_wth

            count = len(df[df["month"] == month_str])

            results.append({
                "period": str(month_str),
                "income": float(tot_inc),
                "expense": float(tot_exp),
                "net": float(net),
                "revenue": float(rev),
                "cogs": float(cogs),
                "operating_expense": float(op_exp),
                "gross_profit": float(gross_p),
                "net_profit": float(net_p),
                "cash_inflow": float(inflow),
                "cash_outflow": float(outflow),
                "transaction_count": count
            })

        return results

    @staticmethod
    def aggregate_categories(transactions: List[Any], category_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Summarizes transactions by category, calculating totals and percentage share.
        """
        if not transactions:
            return []

        cat_totals: Dict[str, Dict[str, Any]] = {}
        total_sum = Decimal("0.00")

        for tx in transactions:
            cat = getattr(tx, "category", None)
            cat_name = cat.name if cat else "Uncategorized"
            cat_type = cat.category_type if cat else "OTHER"
            cat_id = cat.id if cat else None

            # If filtering by type (e.g. only EXPENSE or only INCOME)
            t_type = getattr(tx, "transaction_type", "")
            if category_type_filter:
                if category_type_filter.upper() == "INCOME" and t_type not in ["Revenue", "Other Income"]:
                    continue
                elif category_type_filter.upper() == "EXPENSE" and t_type not in ["Operating Expense", "Cost of Goods Sold"]:
                    continue

            amt = quantize_dec(getattr(tx, "amount", 0))
            total_sum += amt

            if cat_name not in cat_totals:
                cat_totals[cat_name] = {
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "category_type": cat_type,
                    "total_amount": Decimal("0.00"),
                    "transaction_count": 0
                }

            cat_totals[cat_name]["total_amount"] += amt
            cat_totals[cat_name]["transaction_count"] += 1

        results = []
        for cat_name, data in sorted(cat_totals.items(), key=lambda x: x[1]["total_amount"], reverse=True):
            pct = calculate_ratio(data["total_amount"], total_sum) or Decimal("0.00")
            results.append({
                "category_id": data["category_id"],
                "category_name": data["category_name"],
                "category_type": data["category_type"],
                "total_amount": float(quantize_dec(data["total_amount"])),
                "percentage": float(quantize_dec(pct)),
                "transaction_count": data["transaction_count"]
            })

        return results
