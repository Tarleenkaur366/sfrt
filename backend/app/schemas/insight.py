from pydantic import BaseModel
from typing import Optional, List, Any

class FinancialInsight(BaseModel):
    id: str
    title: str
    description: str
    metric_name: str
    metric_value: Optional[str] = None
    period: str
    calculation_explanation: str
    severity: str  # info, warning, danger, success
    category: str  # cash_flow, profitability, expense, revenue, data_quality

class InsightListResponse(BaseModel):
    total_insights: int
    insights: List[FinancialInsight]
