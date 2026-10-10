from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_id = Column(String(100), nullable=True, index=True)
    custom_note = Column(String(255), nullable=True)

    certificate_code = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), default=CertificateStatus.PENDING.value, nullable=False, index=True)
    
    error_message = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    job = relationship("GenerationJob", back_populates="certificates")
