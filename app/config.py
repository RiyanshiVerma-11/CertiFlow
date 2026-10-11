from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CertiFlow"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Enterprise Bulk Certificate Generation & Verification Engine"
    API_V1_STR: str = "/api/v1"

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage" / "certificates"
    TEMP_DIR: Path = BASE_DIR / "storage" / "temp"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'certiflow.db'}"

    # Generator settings
    MAX_BATCH_SIZE: int = 1000
    DEFAULT_ISSUER: str = "Aereo Engineering Academy"
    BATCH_COMMIT_SIZE: int = 20
    VERIFICATION_BASE_URL: str = "https://certiflow-w2h9.onrender.com"

    # Task queue configuration ('background' or 'celery')
    TASK_QUEUE_BACKEND: str = "background"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage abstraction settings ('local' or 's3')
    STORAGE_BACKEND: str = "local"
    S3_BUCKET_NAME: str = "certiflow-storage"
    S3_REGION_NAME: str = "ap-south-1"
    S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    STORAGE_RETENTION_HOURS: int = 48

    # Rate limiting & security (Generous default for local evaluation & automated testing)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    API_KEY: str = ""  # If left empty, API is open for local evaluation mode

    # Pagination settings
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500
    CLEANUP_INTERVAL_MINUTES: int = 60

    # Automated email dispatch settings (SMTP / AWS SES)
    EMAIL_DISPATCH_ENABLED: bool = False
    EMAIL_PROVIDER: str = "smtp"  # 'smtp', 'ses', or 'mock'
    SMTP_HOST: str = "smtp.mailgun.org"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "certificates@aereo.io"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()

# Ensure required storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
