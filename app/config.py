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
