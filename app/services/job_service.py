import csv
import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.job import GenerationJob, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import (
    JobCreateRequest,
    JobStatusResponse,
    JobFailureDetail,
)
from app.schemas.certificate import RecipientInput, CertificateResponse
from app.services.certificate_generator import CertificateGenerator
from app.services.zip_service import ZipService

logger = logging.getLogger("certiflow.jobs")


class JobService:
    """Orchestrates job lifecycle, background bulk processing, and fault isolation."""

    @classmethod
    def create_job(cls, db: Session, request: JobCreateRequest) -> GenerationJob:
        """Creates a new GenerationJob and prepares pending certificate records."""
        job_id = str(uuid.uuid4())

        job = GenerationJob(
            id=job_id,
            title=request.title,
            issuer_name=request.issuer_name,
            issue_date=request.issue_date,
            status=JobStatus.PENDING.value,
            total_count=len(request.recipients),
            processed_count=0,
            success_count=0,
            failed_count=0,
        )
        db.add(job)

        # Pre-seed certificate records in PENDING state
        for r in request.recipients:
            cert_id = str(uuid.uuid4())
            short_code = f"CERT-{uuid.uuid4().hex[:8].upper()}"
            cert = Certificate(
                id=cert_id,
                job_id=job_id,
                recipient_name=r.name,
                recipient_email=r.email,
                custom_note=r.custom_note,
                certificate_code=short_code,
                status=CertificateStatus.PENDING.value,
            )
            db.add(cert)

        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def process_bulk_job(cls, job_id: str) -> None:
        """
        Background worker routine that processes certificates with individual fault isolation.
        Ensures a single recipient failure never breaks the batch.
        """
        db = SessionLocal()
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in worker thread.")
                return

            job.status = JobStatus.PROCESSING.value
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

            certificates: List[Certificate] = (
                db.query(Certificate).filter(Certificate.job_id == job_id).all()
            )

            for cert in certificates:
                try:
                    # Defensive check: if email contains simulated failure trigger or invalid characters
                    if "__fail__" in cert.recipient_email:
                        raise ValueError(f"Forced test failure triggered for {cert.recipient_email}")

                    # Render certificate PDF
                    pdf_path = CertificateGenerator.generate_pdf(
                        recipient_name=cert.recipient_name,
                        event_title=job.title,
                        issuer_name=job.issuer_name,
                        issue_date=job.issue_date,
                        certificate_code=cert.certificate_code,
                        custom_note=cert.custom_note,
                    )

                    cert.status = CertificateStatus.SUCCESS.value
                    cert.file_path = str(pdf_path)
                    cert.error_message = None
                    job.success_count += 1

                except Exception as exc:
                    # Fault isolation boundary
                    logger.warning(
                        f"Failed generating certificate for {cert.recipient_name} ({cert.recipient_email}): {exc}"
                    )
                    cert.status = CertificateStatus.FAILED.value
                    cert.error_message = str(exc)
                    job.failed_count += 1

                finally:
                    job.processed_count += 1
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()

            # Final status evaluation
            if job.failed_count == 0 and job.success_count > 0:
                job.status = JobStatus.COMPLETED.value
            elif job.success_count > 0 and job.failed_count > 0:
                job.status = JobStatus.PARTIAL_SUCCESS.value
            else:
                job.status = JobStatus.FAILED.value

            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(
                f"Job {job_id} completed with status {job.status}. "
                f"Success: {job.success_count}, Failed: {job.failed_count}"
            )

        except Exception as err:
            logger.exception(f"Unhandled error while processing job {job_id}: {err}")
            try:
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_summary = str(err)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @classmethod
    def get_job_status(cls, db: Session, job_id: str) -> Optional[JobStatusResponse]:
        """Fetches detailed progress telemetry and failure diagnostics."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        # Build failure details list
        failed_certs = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job_id,
                Certificate.status == CertificateStatus.FAILED.value,
            )
            .all()
        )
        failures = [
            JobFailureDetail(
                recipient_name=c.recipient_name,
                recipient_email=c.recipient_email,
                error=c.error_message or "Unknown processing error",
            )
            for c in failed_certs
        ]

        progress = 0.0
        if job.total_count > 0:
            progress = round((job.processed_count / job.total_count) * 100, 1)

        zip_url = None
        if job.status in [JobStatus.COMPLETED.value, JobStatus.PARTIAL_SUCCESS.value] and job.success_count > 0:
            zip_url = f"/api/v1/jobs/{job.id}/download-zip"

        return JobStatusResponse(
            job_id=job.id,
            title=job.title,
            issuer_name=job.issuer_name,
            issue_date=job.issue_date,
            status=job.status,
            progress_percentage=progress,
            total=job.total_count,
            processed=job.processed_count,
            successful=job.success_count,
            failed=job.failed_count,
            failures=failures,
            certificates_url=f"/api/v1/jobs/{job.id}/certificates",
            zip_download_url=zip_url,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    @classmethod
    def get_job_certificates(cls, db: Session, job_id: str) -> Optional[List[CertificateResponse]]:
        """Retrieves list of all certificates associated with a job."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        certs = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.created_at)
            .all()
        )

        results = []
        for c in certs:
            download_url = (
                f"/api/v1/certificates/{c.id}/download"
                if c.status == CertificateStatus.SUCCESS.value
                else None
            )
            results.append(
                CertificateResponse(
                    id=c.id,
                    job_id=c.job_id,
                    recipient_name=c.recipient_name,
                    recipient_email=c.recipient_email,
                    custom_note=c.custom_note,
                    certificate_code=c.certificate_code,
                    status=c.status,
                    error_message=c.error_message,
                    download_url=download_url,
                    created_at=c.created_at,
                )
            )
        return results

    @classmethod
    def get_job_zip_file(cls, db: Session, job_id: str) -> Optional[Path]:
        """Creates and returns a ZIP file containing all successful certificates for a job."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        successful_certs = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job_id,
                Certificate.status == CertificateStatus.SUCCESS.value,
            )
            .all()
        )

        if not successful_certs:
            return None

        files_to_zip: List[Tuple[str, Path]] = []
        for cert in successful_certs:
            if cert.file_path:
                p = Path(cert.file_path)
                if p.exists():
                    safe_name = f"{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"
                    files_to_zip.append((safe_name, p))

        if not files_to_zip:
            return None

        return ZipService.create_job_zip(job_id, files_to_zip)

    @classmethod
    def parse_csv_to_request(
        cls, file_content: bytes, title: str, issuer_name: str, issue_date: str
    ) -> JobCreateRequest:
        """Parses an uploaded CSV file into a JobCreateRequest."""
        text_stream = io.StringIO(file_content.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)

        if not reader.fieldnames:
            raise ValueError("Uploaded CSV is empty or has no header row.")

        # Normalize field names
        field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
        name_col = next((field_map[k] for k in ["name", "recipient_name", "full_name"] if k in field_map), None)
        email_col = next((field_map[k] for k in ["email", "recipient_email", "email_address"] if k in field_map), None)
        note_col = next((field_map[k] for k in ["note", "custom_note", "distinction", "grade"] if k in field_map), None)

        if not name_col or not email_col:
            raise ValueError(
                f"CSV must contain 'name' and 'email' columns. Detected headers: {list(reader.fieldnames)}"
            )

        recipients: List[RecipientInput] = []
        row_num = 1
        errors = []

        for row in reader:
            row_num += 1
            raw_name = row.get(name_col, "").strip()
            raw_email = row.get(email_col, "").strip()
            raw_note = row.get(note_col, "").strip() if note_col else None

            if not raw_name and not raw_email:
                continue  # skip empty lines

            try:
                recipients.append(
                    RecipientInput(
                        name=raw_name,
                        email=raw_email,
                        custom_note=raw_note or None,
                    )
                )
            except Exception as e:
                errors.append(f"Row {row_num}: {e}")

        if errors:
            raise ValueError(f"CSV validation failed on {len(errors)} rows: {'; '.join(errors[:5])}")

        if not recipients:
            raise ValueError("CSV contains no valid recipient rows.")

        return JobCreateRequest(
            title=title,
            issuer_name=issuer_name,
            issue_date=issue_date,
            recipients=recipients,
        )
