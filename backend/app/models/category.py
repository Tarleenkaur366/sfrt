from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import generate_uuid, utc_now

class FinancialCategory(Base):
    __tablename__ = "financial_categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category_type = Column(String(50), nullable=False)  # INCOME, EXPENSE, TRANSFER, ASSET, LIABILITY, EQUITY
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="categories")
    transactions = relationship("FinancialTransaction", back_populates="category")

    __table_args__ = (
        Index("idx_category_user_name", "user_id", "name"),
    )
