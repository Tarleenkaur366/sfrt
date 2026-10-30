from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from decimal import Decimal

class MetricComparison(BaseModel):
    current: Decimal
    previous: Decimal
    change_amount: Decimal
    percentage_change: Optional[Decimal] = None
    status: str  # increased, decreased, unchanged, not_applicable

class DashboardSummaryResponse(BaseModel):
    currency: str
    start_date: str
    end_date: str
    total_income: Decimal
    total_expenses: Decimal
    net_surplus_deficit: Decimal
    net_cash_movement: Decimal
    total_transactions: int
    avg_monthly_income: Decimal
    avg_monthly_expenses: Decimal
    expense_to_income_ratio: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    gross_profit_margin: Optional[Decimal] = None
    operating_profit: Optional[Decimal] = None
    net_profit: Optional[Decimal] = None
    net_profit_margin: Optional[Decimal] = None
    revenue_growth: Optional[Decimal] = None
    reports_generated_count: int
    alerts: List[Dict[str, Any]] = []

class MonthlyTrendPoint(BaseModel):
    period: str  # YYYY-MM
    income: Decimal
    expense: Decimal
    net: Decimal
    revenue: Decimal
    cogs: Decimal
    operating_expense: Decimal
    net_profit: Decimal
    cash_inflow: Decimal
    cash_outflow: Decimal
    transaction_count: int

class CategoryDistributionPoint(BaseModel):
    category_id: Optional[str]
    category_name: str
    category_type: str
    total_amount: Decimal
    percentage: Decimal
    transaction_count: int

class AnalyticsRevenueResponse(BaseModel):
    currency: str
    start_date: str
    end_date: str
    total_revenue: Decimal
    previous_period_revenue: Decimal
    revenue_growth_pct: Optional[Decimal]
    monthly_trends: List[Dict[str, Any]]
    category_breakdown: List[CategoryDistributionPoint]

class AnalyticsExpenseResponse(BaseModel):
    currency: str
    start_date: str
    end_date: str
    total_expenses: Decimal
    previous_period_expenses: Decimal
    expense_growth_pct: Optional[Decimal]
    monthly_trends: List[Dict[str, Any]]
    category_breakdown: List[CategoryDistributionPoint]
    largest_categories: List[CategoryDistributionPoint]

class AnalyticsCashFlowResponse(BaseModel):
    currency: str
    start_date: str
    end_date: str
    opening_balance: Decimal
    total_inflows: Decimal
    total_outflows: Decimal
    net_cash_movement: Decimal
    estimated_closing_balance: Decimal
    monthly_trends: List[Dict[str, Any]]

class AnalyticsProfitLossResponse(BaseModel):
    currency: str
    start_date: str
    end_date: str
    revenue: Decimal
    cost_of_goods_sold: Decimal
    gross_profit: Decimal
    gross_profit_margin_pct: Optional[Decimal]
    operating_expenses: Decimal
    operating_profit: Decimal
    operating_profit_margin_pct: Optional[Decimal]
    other_income: Decimal
    other_expenses: Decimal
    net_profit: Decimal
    net_profit_margin_pct: Optional[Decimal]
    monthly_trends: List[Dict[str, Any]]
