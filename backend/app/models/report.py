from sqlalchemy import Column, String, DateTime, Text, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import generate_uuid, utc_now

class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False, index=True)  # INCOME_EXPENSE, PROFIT_LOSS, CASH_FLOW, EXPENSE_ANALYSIS, REVENUE_ANALYSIS, FINANCIAL_PERFORMANCE, CUSTOM
    title = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    report_parameters = Column(Text, nullable=True)  # JSON-encoded parameters
    summary_metrics = Column(Text, nullable=True)     # JSON-encoded calculated figures
    detailed_data = Column(Text, nullable=True)       # JSON-encoded rows & breakdown
    generation_status = Column(String(50), default="COMPLETED", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("idx_report_user_created", "user_id", "created_at"),
        Index("idx_report_user_type", "user_id", "report_type"),
    )
