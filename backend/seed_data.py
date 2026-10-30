from datetime import date, timedelta
from decimal import Decimal
from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.category import FinancialCategory
from app.models.transaction import FinancialTransaction
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegisterRequest
from app.services.calculation_engine import quantize_dec
from app.services.reporting_engine import SmartReportingEngine

def seed_sample_data():
    """
    Seeds a clearly identified sample account and labeled sample transactions (is_sample=True).
    Does NOT overwrite or delete any existing real user data.
    """
    init_db()
    db = SessionLocal()
    try:
        sample_email = "demo@example.com"
        user = db.query(User).filter(User.email == sample_email).first()
        if not user:
            print("Creating sample demo user: demo@example.com / DemoPassword123!")
            user = AuthService.register_user(
                db,
                UserRegisterRequest(
                    full_name="Demo Business Analyst",
                    email=sample_email,
                    password="DemoPassword123!",
                    business_name="Acme Financial Services Demo",
                    default_currency="INR"
                )
            )
        else:
            print("Demo user demo@example.com already exists. Checking sample transactions...")

        # Count existing sample transactions
        existing_samples = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user.id,
            FinancialTransaction.is_sample == True
        ).count()

        if existing_samples > 0:
            print(f"Sample data already present ({existing_samples} sample transactions). Skipping insertion.")
            return

        # Fetch user categories
        categories = {c.name: c for c in db.query(FinancialCategory).filter(FinancialCategory.user_id == user.id).all()}

        today = date.today()
        # Create realistic chronological sample transactions across past 6 months
        sample_records = [
            # Month -5
            (today - timedelta(days=150), "Client IT Consulting", "Revenue", "Service Revenue", Decimal("95000.00"), "Bank Transfer", "INV-2026-051"),
            (today - timedelta(days=148), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-MAY-26"),
            (today - timedelta(days=145), "Staff Salaries May", "Operating Expense", "Salaries", Decimal("48000.00"), "Bank Transfer", "PAY-2026-05"),
            (today - timedelta(days=140), "Cloud Hosting & Subscriptions", "Operating Expense", "Software", Decimal("6500.00"), "Credit Card", "SUB-MAY-01"),

            # Month -4
            (today - timedelta(days=120), "Corporate Training Project", "Revenue", "Service Revenue", Decimal("110000.00"), "Bank Transfer", "INV-2026-062"),
            (today - timedelta(days=118), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-JUN-26"),
            (today - timedelta(days=115), "Staff Salaries June", "Operating Expense", "Salaries", Decimal("48000.00"), "Bank Transfer", "PAY-2026-06"),
            (today - timedelta(days=110), "Hardware Inventory Replenishment", "Cost of Goods Sold", "Inventory", Decimal("22000.00"), "Bank Transfer", "PO-JUN-09"),

            # Month -3
            (today - timedelta(days=90), "Software License Sales", "Revenue", "Sales Revenue", Decimal("135000.00"), "Bank Transfer", "INV-2026-073"),
            (today - timedelta(days=88), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-JUL-26"),
            (today - timedelta(days=85), "Staff Salaries July", "Operating Expense", "Salaries", Decimal("50000.00"), "Bank Transfer", "PAY-2026-07"),
            (today - timedelta(days=80), "Digital Marketing Campaigns", "Operating Expense", "Marketing", Decimal("14500.00"), "Credit Card", "MKT-JUL-01"),
            (today - timedelta(days=75), "Utilities & Internet", "Operating Expense", "Utilities", Decimal("4200.00"), "UPI", "UTIL-JUL-26"),

            # Month -2
            (today - timedelta(days=60), "Custom Development Project Phase 1", "Revenue", "Service Revenue", Decimal("140000.00"), "Bank Transfer", "INV-2026-084"),
            (today - timedelta(days=58), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-AUG-26"),
            (today - timedelta(days=55), "Staff Salaries August", "Operating Expense", "Salaries", Decimal("50000.00"), "Bank Transfer", "PAY-2026-08"),
            (today - timedelta(days=50), "Production Components", "Cost of Goods Sold", "Inventory", Decimal("28000.00"), "Bank Transfer", "PO-AUG-14"),

            # Month -1
            (today - timedelta(days=30), "Custom Development Project Phase 2", "Revenue", "Service Revenue", Decimal("165000.00"), "Bank Transfer", "INV-2026-095"),
            (today - timedelta(days=28), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-SEP-26"),
            (today - timedelta(days=25), "Staff Salaries September", "Operating Expense", "Salaries", Decimal("52000.00"), "Bank Transfer", "PAY-2026-09"),
            (today - timedelta(days=20), "Search Engine & Social Ads", "Operating Expense", "Marketing", Decimal("16500.00"), "Credit Card", "MKT-SEP-01"),
            (today - timedelta(days=15), "Office Stationery & Supplies", "Operating Expense", "Office Expenses", Decimal("3800.00"), "UPI", "OFF-SEP-26"),

            # Current month
            (today - timedelta(days=7), "Annual Maintenance Retainer", "Revenue", "Service Revenue", Decimal("80000.00"), "Bank Transfer", "INV-2026-101"),
            (today - timedelta(days=4), "Office Lease Payment", "Operating Expense", "Rent", Decimal("32000.00"), "Bank Transfer", "RENT-OCT-26"),
            (today - timedelta(days=2), "SaaS Tool Stack", "Operating Expense", "Software", Decimal("7200.00"), "Credit Card", "SUB-OCT-01")
        ]

        print(f"Adding {len(sample_records)} labeled sample transactions for demonstration...")
        for tx_date, desc, t_type, cat_name, amt, method, ref in sample_records:
            cat = categories.get(cat_name)
            tx = FinancialTransaction(
                user_id=user.id,
                category_id=cat.id if cat else None,
                transaction_date=tx_date,
                description=f"[SAMPLE] {desc}",
                transaction_type=t_type,
                amount=quantize_dec(amt),
                currency="INR",
                payment_method=method,
                reference_number=ref,
                notes="Illustrative sample transaction for testing and demonstration.",
                is_sample=True
            )
            db.add(tx)

        db.commit()

        # Generate sample baseline report
        SmartReportingEngine.generate_report(
            db=db,
            user_id=user.id,
            report_type="PROFIT_LOSS",
            start_date=today - timedelta(days=180),
            end_date=today,
            currency="INR",
            title="[SAMPLE] H2 Baseline Profit and Loss Statement",
            notes="Sample demonstration report generated by seed utility."
        )

        print("Sample dataset seeded successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
