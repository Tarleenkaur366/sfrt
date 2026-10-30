from typing import Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.insight import InsightListResponse, FinancialInsight
from app.routers.deps import get_current_user
from app.services.insight_engine import SmartInsightEngine

router = APIRouter(prefix="/insights", tags=["Financial Insights"])

@router.get("", response_model=InsightListResponse)
def get_insights(
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
        start_date = date(end_date.year, 1, 1) if (end_date - date(end_date.year, 1, 1)).days > 30 else (end_date - timedelta(days=90))

    raw_insights = SmartInsightEngine.generate_insights(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        currency=curr
    )

    items = [FinancialInsight(**ins) for ins in raw_insights]
    return InsightListResponse(
        total_insights=len(items),
        insights=items
    )
