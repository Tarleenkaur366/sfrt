from sqlalchemy import Column, String, DateTime, Text, Date, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import generate_uuid, utc_now

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("financial_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(50), nullable=True)  # Cash, Bank Transfer, UPI, Credit Card, Debit Card, Cheque, Other
    reference_number = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    is_sample = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="transactions")
    category = relationship("FinancialCategory", back_populates="transactions")

    __table_args__ = (
        Index("idx_tx_user_date", "user_id", "transaction_date"),
        Index("idx_tx_user_type", "user_id", "transaction_type"),
        Index("idx_tx_user_ref", "user_id", "reference_number"),
    )
