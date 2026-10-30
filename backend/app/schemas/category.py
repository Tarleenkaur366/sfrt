from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

VALID_CATEGORY_TYPES = [
    "INCOME",
    "EXPENSE",
    "TRANSFER",
    "ASSET",
    "LIABILITY",
    "EQUITY"
]

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category_type: str = Field(..., description="INCOME, EXPENSE, TRANSFER, ASSET, LIABILITY, EQUITY")
    description: Optional[str] = Field(None, max_length=255)

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category_type: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    category_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
