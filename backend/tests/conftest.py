import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.category import FinancialCategory
from app.models.transaction import FinancialTransaction
from app.utils.security import hash_password, create_access_token

# Test in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(
        full_name="Test Financial Analyst",
        email="analyst@example.com",
        password_hash=hash_password("SecurePassword123!"),
        business_name="Test Corp",
        default_currency="INR",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Add starter category
    cat = FinancialCategory(
        user_id=user.id,
        name="Consulting Revenue",
        category_type="INCOME",
        description="Consulting income"
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"sub": test_user.id, "email": test_user.email})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_user(db_session):
    user = User(
        full_name="Other User",
        email="other@example.com",
        password_hash=hash_password("OtherPassword123!"),
        default_currency="INR",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def other_auth_headers(other_user):
    token = create_access_token({"sub": other_user.id, "email": other_user.email})
    return {"Authorization": f"Bearer {token}"}
