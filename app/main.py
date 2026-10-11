from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from sqlalchemy import text
from app.config import settings
from app.database import Base, engine
from app.api.v1.router import api_router


from app.services.task_queue import recover_interrupted_jobs
from app.services.cleanup_service import StorageCleanupService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    Base.metadata.create_all(bind=engine)
    # Automatically migrate SQLite schema for added columns if DB was pre-existing
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE certificates ADD COLUMN recipient_id VARCHAR(100)"))
            conn.commit()
        except Exception:
            pass  # Column already exists

    # Crash recovery: scan for interrupted jobs from prior process crash/restart
    recover_interrupted_jobs()

    # Lifecycle cleanup: enforce TTL on expired temp files
    StorageCleanupService.run_retention_cleanup()

    # Seed default sample credential for instant recruiter verification if empty
    seed_initial_demo_if_empty()

    yield


def seed_initial_demo_if_empty():
    """Seeds an initial authentic sample credential on fresh deployment for instant recruiter verification."""
    from app.database import SessionLocal
    from app.models.certificate import Certificate, CertificateStatus
    from app.models.job import GenerationJob, JobStatus
    from app.services.certificate_generator import CertificateGenerator
    import uuid

    db = SessionLocal()
    try:
        existing = db.query(Certificate).filter(Certificate.certificate_code == "CERT-AEREO-DEMO-001").first()
        if not existing:
            job_id = str(uuid.uuid4())
            demo_job = GenerationJob(
                id=job_id,
                title="AEREO Autonomous Drone Navigation & Geospatial Fleet Systems",
                issuer_name="AEREO Directorate of Flight Operations & Aerial Systems",
                issue_date="2026-10-11",
                total_records=1,
                successful_records=1,
                failed_records=0,
                status=JobStatus.COMPLETED.value,
            )
            db.add(demo_job)
            db.commit()

            cert_path = settings.STORAGE_DIR / "CERT-AEREO-DEMO-001.pdf"
            settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            CertificateGenerator.generate_pdf(
                recipient_name="Riyanshi Verma",
                event_title="AEREO Autonomous Drone Navigation & Geospatial Fleet Systems",
                issuer_name="AEREO Directorate of Flight Operations & Aerial Systems",
                issue_date="2026-10-11",
                certificate_code="CERT-AEREO-DEMO-001",
                custom_note="Top 1% Flight Performance • Honors Distinction",
                output_path=cert_path,
            )

            demo_cert = Certificate(
                id=str(uuid.uuid4()),
                job_id=job_id,
                recipient_name="Riyanshi Verma",
                recipient_email="riyanshi.verma@aereo.io",
                recipient_id="AEREO-PILOT-01",
                certificate_code="CERT-AEREO-DEMO-001",
                custom_note="Top 1% Flight Performance • Honors Distinction",
                status=CertificateStatus.SUCCESS.value,
                file_path=str(cert_path),
            )
            db.add(demo_cert)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for open client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static assets
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container and uptime monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the interactive CertiFlow Landing Page & App Console."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "CertiFlow API is live! Visit /docs for the interactive Swagger documentation.",
        "docs": "/docs",
    }
