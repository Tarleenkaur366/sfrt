from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

VALID_TRANSACTION_TYPES = [
    "Revenue",
    "Other Income",
    "Operating Expense",
    "Cost of Goods Sold",
    "Asset Purchase",
    "Liability Payment",
    "Owner Contribution",
    "Owner Withdrawal",
    "Transfer"
]

class TransactionCreate(BaseModel):
    transaction_date: date
    description: str = Field(..., min_length=2, max_length=255)
    transaction_type: str
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("INR", min_length=3, max_length=3)
    category_id: Optional[str] = None
    payment_method: Optional[str] = Field("Bank Transfer", max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_sample: bool = False

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        for t in VALID_TRANSACTION_TYPES:
            if v.strip().lower() == t.lower():
                return t
        raise ValueError(f"Invalid transaction type. Allowed: {', '.join(VALID_TRANSACTION_TYPES)}")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

class TransactionUpdate(BaseModel):
    transaction_date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=2, max_length=255)
    transaction_type: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    category_id: Optional[str] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        for t in VALID_TRANSACTION_TYPES:
            if v.strip().lower() == t.lower():
                return t
        raise ValueError(f"Invalid transaction type. Allowed: {', '.join(VALID_TRANSACTION_TYPES)}")

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_type: Optional[str] = None
    transaction_date: date
    description: str
    transaction_type: str
    amount: Decimal
    currency: str
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_sample: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
