from datetime import date
from decimal import Decimal
from app.services.insight_engine import SmartInsightEngine
from app.models.transaction import FinancialTransaction
from app.models.category import FinancialCategory
from app.services.calculation_engine import quantize_dec

def test_empty_records_insight(db_session, test_user):
    insights = SmartInsightEngine.generate_insights(
        db=db_session,
        user_id=test_user.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31)
    )
    assert len(insights) == 1
    assert insights[0]["id"] == "ins-empty-data"

def test_net_deficit_and_concentration_insights(db_session, test_user):
    cat_rent = FinancialCategory(user_id=test_user.id, name="Commercial Rent", category_type="EXPENSE")
    db_session.add(cat_rent)
    db_session.commit()

    # Expenses (70k) > Income (20k)
    tx_inc = FinancialTransaction(
        user_id=test_user.id,
        transaction_date=date(2026, 4, 5),
        description="Small Service Gig",
        transaction_type="Revenue",
        amount=quantize_dec("20000.00"),
        currency="INR"
    )
    tx_exp = FinancialTransaction(
        user_id=test_user.id,
        category_id=cat_rent.id,
        transaction_date=date(2026, 4, 10),
        description="Office Rent",
        transaction_type="Operating Expense",
        amount=quantize_dec("70000.00"),
        currency="INR"
    )
    db_session.add_all([tx_inc, tx_exp])
    db_session.commit()

    insights = SmartInsightEngine.generate_insights(
        db=db_session,
        user_id=test_user.id,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
        currency="INR"
    )

    ids = [i["id"] for i in insights]
    assert "ins-net-deficit" in ids
    assert "ins-dominant-expense" in ids
