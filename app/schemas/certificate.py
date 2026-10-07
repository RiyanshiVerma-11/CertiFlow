import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Full name of recipient")
    email: str = Field(..., description="Valid email address of recipient")
    custom_note: Optional[str] = Field(None, max_length=200, description="Optional distinction or note")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be empty or whitespace only")
        return trimmed

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError(f"Invalid email address format: '{v}'")
        return trimmed


class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    custom_note: Optional[str] = None
    certificate_code: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CertificateVerifyResponse(BaseModel):
    is_valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    title: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[str] = None
    custom_note: Optional[str] = None
    issued_at: Optional[datetime] = None
    status: str
    message: str
