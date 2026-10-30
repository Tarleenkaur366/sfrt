from datetime import date
from decimal import Decimal
from app.services.reporting_engine import SmartReportingEngine
from app.models.transaction import FinancialTransaction
from app.models.category import FinancialCategory
from app.services.calculation_engine import quantize_dec

def test_generate_profit_loss_report(db_session, test_user):
    # Add revenue and COGS transactions
    cat_rev = FinancialCategory(user_id=test_user.id, name="Sales Revenue", category_type="INCOME")
    cat_cogs = FinancialCategory(user_id=test_user.id, name="Inventory", category_type="EXPENSE")
    cat_op = FinancialCategory(user_id=test_user.id, name="Salaries", category_type="EXPENSE")
    db_session.add_all([cat_rev, cat_cogs, cat_op])
    db_session.commit()

    tx1 = FinancialTransaction(
        user_id=test_user.id,
        category_id=cat_rev.id,
        transaction_date=date(2026, 2, 10),
        description="Software Product Sales",
        transaction_type="Revenue",
        amount=quantize_dec("150000.00"),
        currency="INR"
    )
    tx2 = FinancialTransaction(
        user_id=test_user.id,
        category_id=cat_cogs.id,
        transaction_date=date(2026, 2, 12),
        description="Direct Server & License Costs",
        transaction_type="Cost of Goods Sold",
        amount=quantize_dec("30000.00"),
        currency="INR"
    )
    tx3 = FinancialTransaction(
        user_id=test_user.id,
        category_id=cat_op.id,
        transaction_date=date(2026, 2, 15),
        description="Operations Team Salaries",
        transaction_type="Operating Expense",
        amount=quantize_dec("45000.00"),
        currency="INR"
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    report = SmartReportingEngine.generate_report(
        db=db_session,
        user_id=test_user.id,
        report_type="PROFIT_LOSS",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
        currency="INR",
        title="Q1 P&L Report"
    )

    assert report.id is not None
    assert report.report_type == "PROFIT_LOSS"
    assert report.title == "Q1 P&L Report"
    assert report.generation_status == "COMPLETED"
    assert "Cost of Goods Sold" in report.report_parameters
    assert "150000" in report.summary_metrics

def test_generate_cash_flow_report(db_session, test_user):
    tx = FinancialTransaction(
        user_id=test_user.id,
        transaction_date=date(2026, 3, 1),
        description="Owner Capital Injection",
        transaction_type="Owner Contribution",
        amount=quantize_dec("50000.00"),
        currency="INR"
    )
    db_session.add(tx)
    db_session.commit()

    report = SmartReportingEngine.generate_report(
        db=db_session,
        user_id=test_user.id,
        report_type="CASH_FLOW",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        currency="INR",
        opening_cash_balance=10000.0
    )

    assert report.id is not None
    assert "opening_cash_balance" in report.summary_metrics
