import csv
import io
import logging
import math
import time
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
from app.schemas.certificate import (
    RecipientInput,
    CertificateResponse,
    PaginatedCertificateResponse,
    validate_recipient_data,
)
from app.services.certificate_generator import CertificateGenerator
from app.services.storage_service import get_storage_provider
from app.services.zip_service import ZipService

logger = logging.getLogger("certiflow.jobs")


class JobService:
    """Orchestrates job lifecycle, background bulk processing, batch commits, and zero-drop fault isolation."""

    @classmethod
    def create_job(cls, db: Session, request: JobCreateRequest) -> GenerationJob:
        """
        Creates a new GenerationJob and prepares certificate records.
        Applies zero-drop validation: individual invalid recipients are flagged as FAILED upfront
        with isolated diagnostic messages, while valid recipients are queued for generation.
        """
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

        # Pre-seed certificate records with fault-isolated pre-validation
        for r in request.recipients:
            cert_id = str(uuid.uuid4())
            short_code = f"CERT-{uuid.uuid4().hex[:8].upper()}"

            is_valid, validation_error = validate_recipient_data(r.name, r.email)
            initial_status = CertificateStatus.PENDING.value if is_valid else CertificateStatus.FAILED.value
            initial_error = None if is_valid else f"Validation Error: {validation_error}"

            cert = Certificate(
                id=cert_id,
                job_id=job_id,
                recipient_name=r.name,
                recipient_email=r.email,
                recipient_id=r.recipient_id,
                custom_note=r.custom_note,
                certificate_code=short_code,
                status=initial_status,
                error_message=initial_error,
            )
            db.add(cert)

        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def process_bulk_job(cls, job_id: str) -> None:
        """
        Background worker routine that processes certificates with individual fault isolation
        and batched database commits to prevent SQLite write-lock contention.
        """
        db = SessionLocal()
        storage = get_storage_provider()
        batch_size = max(1, settings.BATCH_COMMIT_SIZE)
        uncommitted_count = 0

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
                    # Check if already marked as FAILED during zero-drop ingestion
                    if cert.status == CertificateStatus.FAILED.value:
                        job.failed_count += 1
                        continue

                    # Render certificate PDF directly in-memory
                    pdf_bytes = CertificateGenerator.generate_pdf_bytes(
                        recipient_name=cert.recipient_name,
                        event_title=job.title,
                        issuer_name=job.issuer_name,
                        issue_date=job.issue_date,
                        certificate_code=cert.certificate_code,
                        recipient_id=cert.recipient_id,
                        custom_note=cert.custom_note,
                    )

                    # Persist through decoupled storage provider
                    storage_key = storage.save_certificate(cert.certificate_code, pdf_bytes)

                    cert.status = CertificateStatus.SUCCESS.value
                    cert.file_path = storage_key
                    cert.error_message = None
                    job.success_count += 1

                    # Automated Email Delivery (if enabled in settings)
                    if settings.EMAIL_DISPATCH_ENABLED:
                        try:
                            from app.services.email_service import EmailDispatcher
                            EmailDispatcher.dispatch_certificate_email(
                                recipient_name=cert.recipient_name,
                                recipient_email=cert.recipient_email,
                                certificate_code=cert.certificate_code,
                                event_title=job.title,
                                issuer_name=job.issuer_name,
                                pdf_bytes=pdf_bytes,
                                custom_note=cert.custom_note,
                            )
                        except Exception as email_err:
                            logger.warning(f"Email delivery error for {cert.recipient_email}: {email_err}")

                except Exception as exc:
                    # Fault isolation boundary: isolate failure and continue batch
                    logger.warning(
                        f"Failed generating certificate for {cert.recipient_name} ({cert.recipient_email}): {exc}"
                    )
                    cert.status = CertificateStatus.FAILED.value
                    cert.error_message = str(exc)
                    job.failed_count += 1

                finally:
                    job.processed_count += 1
                    job.updated_at = datetime.now(timezone.utc)
                    uncommitted_count += 1

                    # BATCH COMMIT: Commits in batches to avoid SQLite lock contention
                    if uncommitted_count >= batch_size:
                        try:
                            db.commit()
                            uncommitted_count = 0
                        except Exception as commit_err:
                            logger.warning(f"Batch commit retry on database: {commit_err}")
                            time.sleep(0.05)
                            db.commit()
                            uncommitted_count = 0

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
    def get_job_certificates(
        cls,
        db: Session,
        job_id: str,
        page: int = 1,
        limit: int = 50,
        status_filter: Optional[str] = None,
    ) -> Optional[PaginatedCertificateResponse]:
        """
        Retrieves paginated list of certificates associated with a job.
        Includes total count, pagination metadata, and download links.
        """
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return None

        query = db.query(Certificate).filter(Certificate.job_id == job_id)
        if status_filter:
            query = query.filter(Certificate.status == status_filter.upper())

        total = query.count()
        limit = max(1, min(limit, settings.MAX_PAGE_SIZE))
        page = max(1, page)
        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

        certs = (
            query.order_by(Certificate.created_at)
            .offset((page - 1) * limit)
            .limit(limit)
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
                    recipient_id=c.recipient_id,
                    custom_note=c.custom_note,
                    certificate_code=c.certificate_code,
                    status=c.status,
                    error_message=c.error_message,
                    download_url=download_url,
                    created_at=c.created_at,
                )
            )

        return PaginatedCertificateResponse(
            items=results,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=(page < total_pages),
            has_prev=(page > 1),
        )

    @classmethod
    def get_job_zip_buffer(cls, db: Session, job_id: str) -> Optional[io.BytesIO]:
        """
        Packages all successful certificates into an in-memory ZIP buffer.
        Eliminates duplicate files on disk and prevents storage bloat.
        """
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

        storage = get_storage_provider()
        files_to_zip: List[Tuple[str, bytes]] = []

        for cert in successful_certs:
            if cert.file_path:
                pdf_bytes = storage.get_certificate_bytes(cert.file_path)
                if pdf_bytes:
                    safe_name = f"{cert.recipient_name.replace(' ', '_')}_{cert.certificate_code}.pdf"
                    files_to_zip.append((safe_name, pdf_bytes))

        if not files_to_zip:
            return None

        return ZipService.create_in_memory_zip(files_to_zip)

    @classmethod
    def get_job_zip_file(cls, db: Session, job_id: str) -> Optional[Path]:
        """Creates and returns a temporary ZIP file containing all successful certificates for a job."""
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
        """
        Parses an uploaded CSV file into a JobCreateRequest.
        Applies zero-drop ingestion: rows with invalid emails or formatting are ingested
        and isolated at the certificate stage without rejecting the entire CSV upload!
        """
        text_stream = io.StringIO(file_content.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)

        if not reader.fieldnames:
            raise ValueError("Uploaded CSV is empty or has no header row.")

        # Normalize field names
        field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
        name_col = next((field_map[k] for k in ["name", "recipient_name", "full_name"] if k in field_map), None)
        email_col = next((field_map[k] for k in ["email", "recipient_email", "email_address"] if k in field_map), None)
        id_col = next((field_map[k] for k in ["recipient_id", "student_id", "id", "roll_no", "roll_number"] if k in field_map), None)
        note_col = next((field_map[k] for k in ["note", "custom_note", "distinction", "grade"] if k in field_map), None)

        if not name_col or not email_col:
            raise ValueError(
                f"CSV must contain 'name' and 'email' columns. Detected headers: {list(reader.fieldnames)}"
            )

        recipients: List[RecipientInput] = []
        row_num = 1

        for row in reader:
            row_num += 1
            raw_name = row.get(name_col, "").strip()
            raw_email = row.get(email_col, "").strip()
            raw_id = row.get(id_col, "").strip() if id_col else None
            raw_note = row.get(note_col, "").strip() if note_col else None

            if not raw_name and not raw_email:
                continue  # skip completely empty lines

            # Zero-drop fault isolation: Add the row to recipients.
            # Any validation discrepancies (e.g. invalid email format) are isolated per-row
            # during processing, allowing all valid rows to generate successfully!
            recipients.append(
                RecipientInput(
                    name=raw_name,
                    email=raw_email,
                    recipient_id=raw_id or None,
                    custom_note=raw_note or None,
                )
            )

        if not recipients:
            raise ValueError("CSV contains no recipient rows.")

        return JobCreateRequest(
            title=title,
            issuer_name=issuer_name,
            issue_date=issue_date,
            recipients=recipients,
        )

    @classmethod
    def dispatch_job_emails(cls, db: Session, job_id: str) -> dict:
        """
        Manually triggers automated email dispatch for all successfully generated certificates in a job.
        """
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return {"status": "error", "message": f"Job {job_id} not found."}

        successful_certs = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job_id,
                Certificate.status == CertificateStatus.SUCCESS.value,
            )
            .all()
        )

        storage = get_storage_provider()
        from app.services.email_service import EmailDispatcher

        dispatched = []
        for cert in successful_certs:
            if cert.file_path:
                pdf_bytes = storage.get_certificate_bytes(cert.file_path)
                if pdf_bytes:
                    res = EmailDispatcher.dispatch_certificate_email(
                        recipient_name=cert.recipient_name,
                        recipient_email=cert.recipient_email,
                        certificate_code=cert.certificate_code,
                        event_title=job.title,
                        issuer_name=job.issuer_name,
                        pdf_bytes=pdf_bytes,
                        custom_note=cert.custom_note,
                    )
                    dispatched.append(res)

        return {
            "status": "success",
            "job_id": job_id,
            "total_successful": len(successful_certs),
            "dispatched_count": len(dispatched),
            "sample_deliveries": dispatched[:5],
        }
