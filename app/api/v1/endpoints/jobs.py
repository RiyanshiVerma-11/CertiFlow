from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
    Query,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import check_rate_limit, verify_api_key
from app.database import get_db
from app.schemas.job import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from app.schemas.certificate import PaginatedCertificateResponse
from app.services.cleanup_service import StorageCleanupService
from app.services.job_service import JobService
from app.services.task_queue import get_task_dispatcher

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job (JSON)",
    description="Accepts a list of recipients and enqueues an asynchronous background generation task with zero-drop fault isolation.",
    dependencies=[Depends(check_rate_limit), Depends(verify_api_key)],
)
def create_bulk_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = JobService.create_job(db=db, request=request)
    dispatcher = get_task_dispatcher()
    dispatcher.dispatch(job.id, background_tasks)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_count,
        message=f"Bulk certificate generation job accepted ({dispatcher.get_backend_name()}).",
        status_url=f"/api/v1/jobs/{job.id}",
    )


@router.post(
    "/upload-csv",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit bulk certificate generation job via CSV upload",
    description="Parses an uploaded CSV file with zero-drop fault isolation. Invalid rows are isolated without rejecting the entire batch.",
    dependencies=[Depends(check_rate_limit), Depends(verify_api_key)],
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
    dispatcher = get_task_dispatcher()
    dispatcher.dispatch(job.id, background_tasks)

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
    response_model=PaginatedCertificateResponse,
    summary="List generated certificates for job (Paginated)",
    description="Returns paginated certificates for a job with cursor/offset limits (?page=1&limit=50).",
)
def get_job_certificates(
    job_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    status: Optional[str] = Query(None, description="Optional status filter: SUCCESS, FAILED, PENDING"),
    db: Session = Depends(get_db),
):
    paginated_certs = JobService.get_job_certificates(
        db=db,
        job_id=job_id,
        page=page,
        limit=limit,
        status_filter=status,
    )
    if paginated_certs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )
    return paginated_certs


@router.get(
    "/{job_id}/download-zip",
    summary="Download all certificates as a single in-memory ZIP archive",
    description="Streams a compressed ZIP archive in-memory directly to the HTTP response without saving redundant copies on disk.",
)
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    zip_buffer = JobService.get_job_zip_buffer(db=db, job_id=job_id)
    if not zip_buffer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No generated certificates available to compress for job '{job_id}'.",
        )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="certificates_{job_id[:8]}.zip"',
            "Cache-Control": "no-cache",
        },
    )


@router.post(
    "/cleanup",
    summary="Execute automated storage retention & lifecycle cleanup",
    description="Purges expired temporary ZIPs and storage artifacts exceeding the TTL retention policy.",
    dependencies=[Depends(verify_api_key)],
)
def trigger_storage_cleanup(
    retention_hours: Optional[int] = Query(None, ge=1, description="Override retention hours TTL"),
):
    result = StorageCleanupService.run_retention_cleanup(retention_hours=retention_hours)
    return result


@router.post(
    "/{job_id}/dispatch-emails",
    summary="Trigger automated email delivery for all generated certificates",
    description="Dispatches personalized emails with the certificate attached as PDF to all successful recipients.",
    dependencies=[Depends(verify_api_key)],
)
def dispatch_job_emails(job_id: str, db: Session = Depends(get_db)):
    result = JobService.dispatch_job_emails(db=db, job_id=job_id)
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Job not found"),
        )
    return result
