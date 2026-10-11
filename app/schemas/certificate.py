import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_recipient_data(name: Optional[str], email: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validates recipient data quality rules for fault isolation.
    Returns (is_valid, error_reason).
    """
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        return False, "Recipient name cannot be empty or whitespace only"

    cleaned_email = (email or "").strip().lower()
    if not cleaned_email:
        return False, "Recipient email is required and cannot be empty"

    if not EMAIL_REGEX.match(cleaned_email):
        return False, f"Invalid email address format: '{email}'"

    return True, None


class RecipientInput(BaseModel):
    name: str = Field(..., max_length=150, description="Full name of recipient")
    email: str = Field(..., max_length=255, description="Email address of recipient")
    recipient_id: Optional[str] = Field(None, max_length=100, description="Optional participant or student roll/ID")
    custom_note: Optional[str] = Field(None, max_length=200, description="Optional distinction or note")


class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    recipient_id: Optional[str] = None
    custom_note: Optional[str] = None
    certificate_code: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedCertificateResponse(BaseModel):
    items: list[CertificateResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


class CertificateVerifyResponse(BaseModel):
    is_valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    recipient_id: Optional[str] = None
    title: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    custom_note: Optional[str] = None
    issued_at: Optional[datetime] = None
    download_url: Optional[str] = None
    status: str
    message: str
