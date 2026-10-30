from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

VALID_REPORT_TYPES = [
    "INCOME_EXPENSE",
    "PROFIT_LOSS",
    "CASH_FLOW",
    "EXPENSE_ANALYSIS",
    "REVENUE_ANALYSIS",
    "FINANCIAL_PERFORMANCE",
    "CUSTOM"
]

class ReportGenerateRequest(BaseModel):
    report_type: str = Field(..., description="One of: INCOME_EXPENSE, PROFIT_LOSS, CASH_FLOW, EXPENSE_ANALYSIS, REVENUE_ANALYSIS, FINANCIAL_PERFORMANCE, CUSTOM")
    title: Optional[str] = None
    start_date: date
    end_date: date
    currency: Optional[str] = "INR"
    category_ids: Optional[List[str]] = None
    transaction_types: Optional[List[str]] = None
    grouping: Optional[str] = "monthly"  # monthly, quarterly, daily
    opening_cash_balance: Optional[float] = 0.0
    notes: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    user_id: str
    report_type: str
    title: str
    start_date: date
    end_date: date
    currency: str
    report_parameters: Optional[Dict[str, Any]] = None
    summary_metrics: Optional[Dict[str, Any]] = None
    detailed_data: Optional[Dict[str, Any]] = None
    generation_status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
