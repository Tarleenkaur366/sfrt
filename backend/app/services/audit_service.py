from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

class AuditService:
    @staticmethod
    def log(
        db: Session,
        user_id: str,
        action: str,
        record_type: str,
        record_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            record_type=record_type,
            record_id=record_id,
            details=details,
            ip_address=ip_address
        )
        db.add(audit_entry)
        db.commit()
        return audit_entry
