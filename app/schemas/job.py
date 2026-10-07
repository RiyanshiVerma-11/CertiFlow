from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.certificate import RecipientInput


class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, description="Event or certificate title")
    issuer_name: str = Field(
        default="Aereo Engineering Academy",
        min_length=2,
        max_length=150,
        description="Issuing organization or authority",
    )
    issue_date: str = Field(..., min_length=4, max_length=50, description="Date of issuance (e.g., 2026-10-07)")
    recipients: List[RecipientInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of recipients to generate certificates for",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title cannot be empty")
        return trimmed

    @field_validator("recipients")
    @classmethod
    def validate_recipients_non_empty(cls, v: List[RecipientInput]) -> List[RecipientInput]:
        if not v:
            raise ValueError("Recipient list cannot be empty. At least one recipient is required.")
        return v


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    total_recipients: int
    message: str
    status_url: str


class JobFailureDetail(BaseModel):
    recipient_name: str
    recipient_email: str
    error: str


class JobStatusResponse(BaseModel):
    job_id: str
    title: str
    issuer_name: str
    issue_date: str
    status: str
    progress_percentage: float
    total: int
    processed: int
    successful: int
    failed: int
    failures: List[JobFailureDetail] = []
    certificates_url: str
    zip_download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
