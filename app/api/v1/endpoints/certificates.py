from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certificate import Certificate, CertificateStatus
from app.models.job import GenerationJob
from app.schemas.certificate import CertificateVerifyResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get(
    "/{certificate_id}/download",
    summary="Download individual certificate PDF",
    description="Streams the generated PDF certificate for a recipient.",
)
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found.",
        )

    if cert.status != CertificateStatus.SUCCESS.value or not cert.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate generation status is '{cert.status}': {cert.error_message or 'File not available.'}",
        )

    file_path = Path(cert.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate PDF file is missing from storage.",
        )

    filename = f"Certificate_{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
    )


@router.get(
    "/verify/{certificate_code}",
    response_model=CertificateVerifyResponse,
    summary="Verify certificate authenticity by code",
    description="Public verification endpoint to authenticate a certificate and inspect its issuing details.",
)
def verify_certificate(certificate_code: str, db: Session = Depends(get_db)):
    code_cleaned = certificate_code.strip().upper()
    cert = (
        db.query(Certificate)
        .filter(Certificate.certificate_code == code_cleaned)
        .first()
    )

    if not cert or cert.status != CertificateStatus.SUCCESS.value:
        return CertificateVerifyResponse(
            is_valid=False,
            certificate_code=certificate_code,
            status="NOT_FOUND_OR_INVALID",
            message="Certificate credential was not found or has not been successfully issued.",
        )

    job = db.query(GenerationJob).filter(GenerationJob.id == cert.job_id).first()
    title = job.title if job else "Specialist Course"
    issuer = job.issuer_name if job else "Aereo Engineering Academy"
    issue_date = job.issue_date if job else "N/A"

    return CertificateVerifyResponse(
        is_valid=True,
        certificate_code=cert.certificate_code,
        recipient_name=cert.recipient_name,
        title=title,
        issuer_name=issuer,
        issue_date=issue_date,
        custom_note=cert.custom_note,
        issued_at=cert.created_at,
        status="VERIFIED_VALID",
        message="Official verified credential authenticated in CertiFlow registry.",
    )
