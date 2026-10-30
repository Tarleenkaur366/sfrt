from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    business_name: Optional[str] = Field(None, max_length=150)
    default_currency: str = Field("INR", min_length=3, max_length=3)

    @field_validator("default_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    business_name: Optional[str] = Field(None, max_length=150)
    default_currency: Optional[str] = Field(None, min_length=3, max_length=3)

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    business_name: Optional[str] = None
    default_currency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    message: str
    user: UserProfileResponse
    token: Optional[str] = None
