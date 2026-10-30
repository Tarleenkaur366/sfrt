import io
from typing import List, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from sqlalchemy.orm import Session
from app.models.transaction import FinancialTransaction
from app.models.category import FinancialCategory
from app.models.import_job import ImportJob
from app.schemas.transaction import VALID_TRANSACTION_TYPES
from app.services.calculation_engine import quantize_dec

REQUIRED_COLUMNS = ["transaction_date", "description", "amount"]
OPTIONAL_COLUMNS = ["transaction_type", "category", "currency", "payment_method", "reference_number", "notes"]

class ImportService:
    """
    Robust CSV ingestion engine with preview, validation, duplicate detection,
    and safe database persistence.
    """

    @staticmethod
    def preview_csv(
        db: Session,
        user_id: str,
        file_content: bytes,
        file_name: str
    ) -> Dict[str, Any]:
        """
        Parses CSV, checks headers, executes row-level validations,
        checks for duplicates against existing database records, and prepares a preview.
        """
        try:
            # Read using pandas with explicit string types to avoid silent loss
            df = pd.read_csv(io.BytesIO(file_content), dtype=str)
        except Exception as e:
            raise ValueError(f"Unable to parse CSV file: {str(e)}")

        # Normalize column headers (strip spaces, lowercase, replace spaces with underscores)
        normalized_cols = {col: col.strip().lower().replace(" ", "_") for col in df.columns}
        df.rename(columns=normalized_cols, inplace=True)

        # Check required columns
        missing_req = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_req:
            raise ValueError(
                f"Missing required CSV column(s): {', '.join(missing_req)}. "
                f"Required columns are: {', '.join(REQUIRED_COLUMNS)}"
            )

        total_rows = len(df)
        valid_records: List[Dict[str, Any]] = []
        preview_rows: List[Dict[str, Any]] = []
        validation_summary_warnings: List[str] = []

        valid_count = 0
        invalid_count = 0
        duplicate_count = 0

        # Load user categories for reference
        existing_categories = {
            c.name.strip().lower(): c for c in db.query(FinancialCategory).filter(FinancialCategory.user_id == user_id).all()
        }

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed, accounting for header
            errors: List[str] = []
            is_valid = True
            is_dup = False

            # 1. Validate transaction_date
            raw_date = row.get("transaction_date", "")
            parsed_date: Optional[date] = None
            if pd.isna(raw_date) or not str(raw_date).strip():
                errors.append("Transaction date is empty.")
                is_valid = False
            else:
                try:
                    parsed_date = pd.to_datetime(raw_date).date()
                except Exception:
                    errors.append(f"Invalid date format '{raw_date}'. Use YYYY-MM-DD.")
                    is_valid = False

            # 2. Validate description
            raw_desc = row.get("description", "")
            description = str(raw_desc).strip() if not pd.isna(raw_desc) else ""
            if not description:
                errors.append("Description is required.")
                is_valid = False

            # 3. Validate amount
            raw_amt = row.get("amount", "")
            parsed_amt: Optional[Decimal] = None
            if pd.isna(raw_amt) or not str(raw_amt).strip():
                errors.append("Amount is empty.")
                is_valid = False
            else:
                try:
                    clean_amt_str = str(raw_amt).replace(",", "").replace("$", "").replace("₹", "").strip()
                    parsed_amt = Decimal(clean_amt_str)
                    if parsed_amt <= 0:
                        errors.append("Amount must be a positive number.")
                        is_valid = False
                    else:
                        parsed_amt = quantize_dec(parsed_amt)
                except Exception:
                    errors.append(f"Invalid numeric amount '{raw_amt}'.")
                    is_valid = False

            # 4. Validate or default transaction_type
            raw_type = row.get("transaction_type", "")
            transaction_type = "Operating Expense"
            if not pd.isna(raw_type) and str(raw_type).strip():
                clean_type = str(raw_type).strip()
                matched = False
                for vt in VALID_TRANSACTION_TYPES:
                    if clean_type.lower() == vt.lower():
                        transaction_type = vt
                        matched = True
                        break
                if not matched:
                    # Support common synonyms like 'Income' or 'Expense'
                    if clean_type.lower() in ["income", "credit"]:
                        transaction_type = "Revenue"
                    elif clean_type.lower() in ["expense", "debit"]:
                        transaction_type = "Operating Expense"
                    else:
                        errors.append(f"Invalid transaction type '{clean_type}'.")
                        is_valid = False

            # 5. Currency
            raw_curr = row.get("currency", "INR")
            currency = str(raw_curr).strip().upper() if not pd.isna(raw_curr) and str(raw_curr).strip() else "INR"

            # 6. Category
            raw_cat = row.get("category", "")
            category_name = str(raw_cat).strip() if not pd.isna(raw_cat) else "General"

            # 7. Reference number & payment method
            ref_num = str(row.get("reference_number", "")).strip() if not pd.isna(row.get("reference_number")) else None
            payment_method = str(row.get("payment_method", "Bank Transfer")).strip() if not pd.isna(row.get("payment_method")) else "Bank Transfer"
            notes = str(row.get("notes", "")).strip() if not pd.isna(row.get("notes")) else None

            # 8. Duplicate Detection (Documented Strategy):
            # A record is considered a potential duplicate if an existing record for the same user
            # has the exact same transaction_date, description, amount, AND reference_number (or date + desc + amount if no ref).
            if is_valid and parsed_date and parsed_amt:
                dup_q = db.query(FinancialTransaction).filter(
                    FinancialTransaction.user_id == user_id,
                    FinancialTransaction.transaction_date == parsed_date,
                    FinancialTransaction.description == description,
                    FinancialTransaction.amount == parsed_amt,
                    FinancialTransaction.currency == currency
                )
                if ref_num:
                    dup_q = dup_q.filter(FinancialTransaction.reference_number == ref_num)

                existing_tx = dup_q.first()
                if existing_tx:
                    is_dup = True
                    duplicate_count += 1

            if is_valid:
                valid_count += 1
                record_payload = {
                    "row_number": row_num,
                    "transaction_date": parsed_date.isoformat() if parsed_date else None,
                    "description": description,
                    "transaction_type": transaction_type,
                    "category": category_name,
                    "amount": float(parsed_amt) if parsed_amt else 0.0,
                    "currency": currency,
                    "payment_method": payment_method,
                    "reference_number": ref_num,
                    "notes": notes,
                    "is_duplicate": is_dup
                }
                valid_records.append(record_payload)
            else:
                invalid_count += 1

            # Keep sample preview rows (first 100 rows)
            if idx < 100:
                preview_rows.append({
                    "row_number": row_num,
                    "transaction_date": parsed_date.isoformat() if parsed_date else str(raw_date),
                    "description": description or str(raw_desc),
                    "transaction_type": transaction_type,
                    "category": category_name,
                    "amount": float(parsed_amt) if parsed_amt else None,
                    "currency": currency,
                    "payment_method": payment_method,
                    "reference_number": ref_num,
                    "is_valid": is_valid,
                    "is_duplicate": is_dup,
                    "validation_errors": errors
                })

        if invalid_count > 0:
            validation_summary_warnings.append(f"{invalid_count} row(s) contain validation errors and will be omitted.")
        if duplicate_count > 0:
            validation_summary_warnings.append(f"{duplicate_count} row(s) matched existing transactions in the database.")

        return {
            "file_name": file_name,
            "total_rows": total_rows,
            "valid_rows_count": valid_count,
            "invalid_rows_count": invalid_count,
            "duplicate_rows_count": duplicate_count,
            "sample_preview": preview_rows,
            "all_valid_records": valid_records,
            "validation_summary": validation_summary_warnings
        }

    @staticmethod
    def commit_import(
        db: Session,
        user_id: str,
        file_name: str,
        records: List[Dict[str, Any]],
        skip_duplicates: bool = True
    ) -> ImportJob:
        """
        Commits verified records inside a safe database transaction.
        Creates missing categories automatically.
        """
        job = ImportJob(
            user_id=user_id,
            file_name=file_name,
            import_type="CSV",
            status="PENDING",
            total_rows=len(records)
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Cache existing categories
        categories_map = {
            c.name.strip().lower(): c for c in db.query(FinancialCategory).filter(FinancialCategory.user_id == user_id).all()
        }

        successful_rows = 0
        failed_rows = 0
        duplicate_rows = 0
        errors: List[Dict[str, Any]] = []

        try:
            for rec in records:
                if rec.get("is_duplicate", False) and skip_duplicates:
                    duplicate_rows += 1
                    continue

                cat_name = rec.get("category", "General").strip()
                cat_key = cat_name.lower()

                # Get or create category
                category = categories_map.get(cat_key)
                if not category:
                    t_type = rec.get("transaction_type", "Operating Expense")
                    cat_type = "INCOME" if t_type in ["Revenue", "Other Income"] else "EXPENSE"
                    category = FinancialCategory(
                        user_id=user_id,
                        name=cat_name,
                        category_type=cat_type,
                        description="Auto-created during CSV import"
                    )
                    db.add(category)
                    db.flush()
                    categories_map[cat_key] = category

                tx = FinancialTransaction(
                    user_id=user_id,
                    category_id=category.id,
                    transaction_date=date.fromisoformat(rec["transaction_date"]),
                    description=rec["description"],
                    transaction_type=rec.get("transaction_type", "Operating Expense"),
                    amount=quantize_dec(rec["amount"]),
                    currency=rec.get("currency", "INR"),
                    payment_method=rec.get("payment_method", "Bank Transfer"),
                    reference_number=rec.get("reference_number"),
                    notes=rec.get("notes"),
                    is_sample=False
                )
                db.add(tx)
                successful_rows += 1

            job.status = "COMPLETED"
            job.successful_rows = successful_rows
            job.failed_rows = failed_rows
            job.duplicate_rows = duplicate_rows
            job.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.failed_rows = len(records)
            job.error_summary = str(e)
            db.commit()
            raise e

        db.refresh(job)
        return job
