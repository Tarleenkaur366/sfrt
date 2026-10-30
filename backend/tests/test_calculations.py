from decimal import Decimal
from typing import Any
import pytest
from app.services.calculation_engine import (
    FinancialCalculationEngine,
    quantize_dec,
    calculate_percentage_change,
    calculate_ratio
)

class MockTransaction:
    def __init__(self, t_type: str, amount: Any, t_date="2026-03-01", category=None):
        self.transaction_type = t_type
        self.amount = Decimal(str(amount))
        self.transaction_date = t_date
        self.category = category
        self.id = "mock-id"

class MockCategory:
    def __init__(self, name: str, cat_type: str, cat_id="cat-1"):
        self.id = cat_id
        self.name = name
        self.category_type = cat_type

def test_decimal_quantization():
    assert quantize_dec(100.555) == Decimal("100.56")
    assert quantize_dec("45000.1") == Decimal("45000.10")
    assert quantize_dec(None) == Decimal("0.00")
    assert quantize_dec("invalid") == Decimal("0.00")

def test_percentage_change_and_zero_handling():
    # Regular positive change
    pct = calculate_percentage_change(Decimal("150.00"), Decimal("100.00"))
    assert pct == Decimal("50.00")

    # Negative change
    pct_dec = calculate_percentage_change(Decimal("80.00"), Decimal("100.00"))
    assert pct_dec == Decimal("-20.00")

    # Previous value is zero -> must return None (undefined/not meaningful)
    assert calculate_percentage_change(Decimal("100.00"), Decimal("0.00")) is None
    assert calculate_percentage_change(Decimal("100.00"), None) is None

def test_ratio_calculation():
    assert calculate_ratio(Decimal("25.00"), Decimal("100.00")) == Decimal("25.00")
    assert calculate_ratio(Decimal("50.00"), Decimal("0.00")) is None
    assert calculate_ratio(Decimal("50.00"), Decimal("-10.00")) is None

def test_financial_summary_calculations():
    cat_sales = MockCategory("Sales", "INCOME")
    cat_rent = MockCategory("Rent", "EXPENSE")

    txs = [
        MockTransaction("Revenue", "100000.00", category=cat_sales),
        MockTransaction("Other Income", "10000.00"),
        MockTransaction("Cost of Goods Sold", "30000.00"),
        MockTransaction("Operating Expense", "40000.00", category=cat_rent),
        MockTransaction("Asset Purchase", "15000.00"),
        MockTransaction("Owner Contribution", "20000.00"),
        MockTransaction("Transfer", "50000.00")  # Should be neutral
    ]

    summary = FinancialCalculationEngine.calculate_summary(txs, opening_cash=Decimal("5000.00"))

    # Total Income = Revenue (100000) + Other Income (10000) = 110000.00
    assert summary["total_income"] == Decimal("110000.00")

    # Total Expenses = COGS (30000) + Operating Expense (40000) = 70000.00
    assert summary["total_expenses"] == Decimal("70000.00")

    # Net Surplus = 110000 - 70000 = 40000.00
    assert summary["net_surplus_deficit"] == Decimal("40000.00")

    # Gross Profit = Revenue (100000) - COGS (30000) = 70000.00
    assert summary["gross_profit"] == Decimal("70000.00")
    # Gross Profit Margin = (70000 / 100000) * 100 = 70.00%
    assert summary["gross_profit_margin"] == Decimal("70.00")

    # Operating Profit = Gross Profit (70000) - Operating Expense (40000) = 30000.00
    assert summary["operating_profit"] == Decimal("30000.00")

    # Net Profit = (100000 + 10000) - (30000 + 40000) = 40000.00
    assert summary["net_profit"] == Decimal("40000.00")
    assert summary["net_profit_margin"] == Decimal("40.00")

    # Cash Inflows = Revenue (100000) + Other Income (10000) + Owner Contribution (20000) = 130000.00
    assert summary["cash_inflows"] == Decimal("130000.00")

    # Cash Outflows = COGS (30000) + Op Exp (40000) + Asset Purchase (15000) = 85000.00
    assert summary["cash_outflows"] == Decimal("85000.00")

    # Net Cash Movement = 130000 - 85000 = 45000.00
    assert summary["net_cash_movement"] == Decimal("45000.00")

    # Closing Cash = Opening (5000) + Net Movement (45000) = 50000.00
    assert summary["closing_cash"] == Decimal("50000.00")

def test_empty_transactions_handling():
    summary = FinancialCalculationEngine.calculate_summary([], opening_cash=Decimal("0.00"))
    assert summary["total_income"] == Decimal("0.00")
    assert summary["total_expenses"] == Decimal("0.00")
    assert summary["net_surplus_deficit"] == Decimal("0.00")
    assert summary["gross_profit"] == Decimal("0.00")
    assert summary["gross_profit_margin"] is None
    assert summary["net_profit_margin"] is None
    assert summary["transaction_count"] == 0

def test_category_distribution():
    cat_a = MockCategory("Software", "EXPENSE", "c1")
    cat_b = MockCategory("Rent", "EXPENSE", "c2")

    txs = [
        MockTransaction("Operating Expense", "2000.00", category=cat_a),
        MockTransaction("Operating Expense", "8000.00", category=cat_b),
    ]

    cats = FinancialCalculationEngine.aggregate_categories(txs, category_type_filter="EXPENSE")
    assert len(cats) == 2
    # Rent should be first with 80.0% share
    assert cats[0]["category_name"] == "Rent"
    assert cats[0]["total_amount"] == 8000.0
    assert cats[0]["percentage"] == 80.0
    # Software should be second with 20.0% share
    assert cats[1]["category_name"] == "Software"
    assert cats[1]["total_amount"] == 2000.0
    assert cats[1]["percentage"] == 20.0
