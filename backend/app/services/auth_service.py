from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.category import FinancialCategory
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, PasswordChangeRequest, UserProfileUpdateRequest
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.audit_service import AuditService

DEFAULT_STARTER_CATEGORIES = [
    # Income categories
    ("Sales Revenue", "INCOME", "Direct product and merchandise sales revenue"),
    ("Service Revenue", "INCOME", "Professional consulting and client services"),
    ("Salary", "INCOME", "Employment salary and wages"),
    ("Freelance Income", "INCOME", "Contract and freelance income"),
    ("Rental Income", "INCOME", "Property rental proceeds"),
    ("Investment Income", "INCOME", "Dividends, interest, and capital gains"),
    ("Other Income", "INCOME", "Miscellaneous recognized earnings"),
    # Expense categories
    ("Salaries", "EXPENSE", "Staff payroll and contractor compensation"),
    ("Rent", "EXPENSE", "Office, commercial, or residential rent"),
    ("Utilities", "EXPENSE", "Electricity, water, heating, and internet"),
    ("Marketing", "EXPENSE", "Advertising, campaigns, and promotional spend"),
    ("Transportation", "EXPENSE", "Fuel, travel, shipping, and commute"),
    ("Inventory", "EXPENSE", "Cost of goods sold / raw materials / stock"),
    ("Office Expenses", "EXPENSE", "Supplies, printing, stationery, and postage"),
    ("Software", "EXPENSE", "SaaS subscriptions, tools, and IT infrastructure"),
    ("Taxes", "EXPENSE", "Income tax, GST/VAT, and statutory filings"),
    ("Other Expenses", "EXPENSE", "General miscellaneous operational expenses"),
    # Transfer / Equity
    ("Bank Transfer", "TRANSFER", "Internal transfer between user bank accounts"),
    ("Owner Equity", "EQUITY", "Owner capital contribution or withdrawal")
]

class AuthService:
    @staticmethod
    def register_user(db: Session, req: UserRegisterRequest, ip_address: Optional[str] = None) -> User:
        clean_email = req.email.strip().lower()
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            raise ValueError("An account with this email address already exists.")

        user = User(
            full_name=req.full_name.strip(),
            email=clean_email,
            password_hash=hash_password(req.password),
            business_name=req.business_name.strip() if req.business_name else None,
            default_currency=req.default_currency or "INR",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Seed starter categories for user ease of use
        for name, cat_type, desc in DEFAULT_STARTER_CATEGORIES:
            cat = FinancialCategory(
                user_id=user.id,
                name=name,
                category_type=cat_type,
                description=desc
            )
            db.add(cat)
        db.commit()

        AuditService.log(db, user.id, "REGISTER", "USER", user.id, "Account registered successfully", ip_address)
        return user

    @staticmethod
    def authenticate_user(db: Session, req: UserLoginRequest, ip_address: Optional[str] = None) -> Tuple[User, str]:
        clean_email = req.email.strip().lower()
        user = db.query(User).filter(User.email == clean_email).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("Account is currently deactivated.")

        token = create_access_token({"sub": user.id, "email": user.email})
        AuditService.log(db, user.id, "LOGIN", "USER", user.id, "User logged in", ip_address)
        return user, token

    @staticmethod
    def change_password(db: Session, user: User, req: PasswordChangeRequest, ip_address: Optional[str] = None) -> None:
        if not verify_password(req.current_password, user.password_hash):
            raise ValueError("Current password does not match.")

        user.password_hash = hash_password(req.new_password)
        db.commit()
        AuditService.log(db, user.id, "PASSWORD_CHANGE", "USER", user.id, "Password updated", ip_address)

    @staticmethod
    def update_profile(db: Session, user: User, req: UserProfileUpdateRequest, ip_address: Optional[str] = None) -> User:
        if req.full_name is not None:
            user.full_name = req.full_name.strip()
        if req.business_name is not None:
            user.business_name = req.business_name.strip()
        if req.default_currency is not None:
            user.default_currency = req.default_currency.strip().upper()
        
        db.commit()
        db.refresh(user)
        AuditService.log(db, user.id, "PROFILE_UPDATE", "USER", user.id, "Profile updated", ip_address)
        return user
