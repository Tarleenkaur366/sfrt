from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import generate_uuid, utc_now

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    import_type = Column(String(50), default="CSV", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, PREVIEWED, COMPLETED, FAILED
    total_rows = Column(Integer, default=0, nullable=False)
    successful_rows = Column(Integer, default=0, nullable=False)
    failed_rows = Column(Integer, default=0, nullable=False)
    duplicate_rows = Column(Integer, default=0, nullable=False)
    error_summary = Column(Text, nullable=True)  # JSON-encoded array of error objects
    created_at = Column(DateTime, default=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="import_jobs")

    __table_args__ = (
        Index("idx_import_user_created", "user_id", "created_at"),
    )
