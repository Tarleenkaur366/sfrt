from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class ImportPreviewRow(BaseModel):
    row_number: int
    transaction_date: Optional[str]
    description: Optional[str]
    transaction_type: Optional[str]
    category: Optional[str]
    amount: Optional[Decimal]
    currency: Optional[str]
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    is_valid: bool
    is_duplicate: bool
    validation_errors: List[str] = []

class ImportPreviewResponse(BaseModel):
    file_name: str
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    duplicate_rows_count: int
    sample_preview: List[ImportPreviewRow]
    all_valid_records: List[Dict[str, Any]]
    validation_summary: List[str]

class ImportConfirmRequest(BaseModel):
    file_name: str
    records: List[Dict[str, Any]]
    skip_duplicates: bool = True

class ImportJobResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    import_type: str
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    duplicate_rows: int
    error_summary: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
