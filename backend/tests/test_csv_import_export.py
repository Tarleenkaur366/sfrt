from decimal import Decimal
from app.services.import_service import ImportService
from app.utils.csv_sanitizer import sanitize_csv_cell

def test_csv_formula_sanitization():
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|'/C calc'!A0") == "'+cmd|'/C calc'!A0"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("-150.00") == "'-150.00"
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell(None) == ""

def test_csv_preview_and_validation(db_session, test_user):
    csv_bytes = (
        b"transaction_date,description,transaction_type,category,amount,currency\n"
        b"2026-05-01,Client Fee,Revenue,Consulting,50000.00,INR\n"
        b"invalid-date,Bad Row,Revenue,Consulting,2000.00,INR\n"
        b"2026-05-03,Negative Amount,Operating Expense,Office,-500.00,INR\n"
    )

    preview = ImportService.preview_csv(
        db=db_session,
        user_id=test_user.id,
        file_content=csv_bytes,
        file_name="test_upload.csv"
    )

    assert preview["total_rows"] == 3
    assert preview["valid_rows_count"] == 1
    assert preview["invalid_rows_count"] == 2
    assert len(preview["all_valid_records"]) == 1
    assert preview["all_valid_records"][0]["description"] == "Client Fee"
