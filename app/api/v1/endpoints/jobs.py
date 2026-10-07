from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from app.schemas.certificate import CertificateResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job (JSON)",
    description="Accepts a list of recipients and enqueues an asynchronous background generation task. Returns immediate 202 Accepted.",
)
def create_bulk_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = JobService.create_job(db=db, request=request)
    background_tasks.add_task(JobService.process_bulk_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_count,
        message="Bulk certificate generation job accepted and scheduled for background processing.",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post(
    "/upload-csv",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job via CSV upload",
    description="Parses an uploaded CSV file containing recipient names and emails, and triggers asynchronous background processing.",
)
async def create_bulk_job_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file with 'name' and 'email' columns"),
    title: str = Form(..., description="Title of the certificate or event"),
    issuer_name: str = Form("Aereo Engineering Academy", description="Issuer name"),
    issue_date: str = Form(..., description="Date of issuance"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a .csv file.",
        )

    content = await file.read()
    try:
        req = JobService.parse_csv_to_request(
            file_content=content,
            title=title,
            issuer_name=issuer_name,
            issue_date=issue_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    job = JobService.create_job(db=db, request=req)
    background_tasks.add_task(JobService.process_bulk_job, job.id)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_count,
        message=f"CSV parsed successfully ({job.total_count} recipients). Generation scheduled.",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job progress & status telemetry",
    description="Returns real-time execution progress, status, metrics, and failure diagnostics.",
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job_status = JobService.get_job_status(db=db, job_id=job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return job_status


@router.get(
    "/{job_id}/certificates",
    response_model=List[CertificateResponse],
    summary="List generated certificates for job",
    description="Returns all generated recipient certificates, individual download links, and credential codes.",
)
def get_job_certificates(job_id: str, db: Session = Depends(get_db)):
    certs = JobService.get_job_certificates(db=db, job_id=job_id)
    if certs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return certs


@router.get(
    "/{job_id}/download-zip",
    summary="Download all certificates as a single ZIP archive",
    description="Packages all successfully generated certificate PDFs into a ZIP archive and streams it for download.",
)
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    zip_path = JobService.get_job_zip_file(db=db, job_id=job_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No generated certificates available to compress for job '{job_id}'.",
        )

    return FileResponse(
        path=str(zip_path),
        filename=f"certificates_{job_id[:8]}.zip",
        media_type="application/zip",
    )
