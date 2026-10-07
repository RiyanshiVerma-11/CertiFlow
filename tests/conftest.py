import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.config import settings
# Override DATABASE_URL to a file-based test db BEFORE importing engine and SessionLocal
TEST_DB_PATH = settings.BASE_DIR / "test_certiflow.db"
settings.DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

from app.database import Base, engine, SessionLocal, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure test directories and test database are set up and cleaned."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create all tables on the test db
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup tables and test database file after session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass


@pytest.fixture(scope="function")
def db_session():
    """Yields a database session and rolls back transactions after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client():
    """FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client
