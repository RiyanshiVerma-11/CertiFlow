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

    yield


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
