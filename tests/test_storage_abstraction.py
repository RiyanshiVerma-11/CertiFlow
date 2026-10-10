import io
from pathlib import Path
from app.services.storage_service import (
    LocalStorageProvider,
    S3StorageProvider,
    get_storage_provider,
)


def test_local_storage_provider_lifecycle(tmp_path):
    """Validates LocalStorageProvider contract: save, read, exists, and delete."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    code = "CERT-LOCAL-001"
    sample_pdf_bytes = b"%PDF-1.4 sample certificate content"

    # Save
    storage_key = provider.save_certificate(code, sample_pdf_bytes)
    assert Path(storage_key).exists()

    # Exists
    assert provider.exists(storage_key) is True

    # Read
    read_bytes = provider.get_certificate_bytes(storage_key)
    assert read_bytes == sample_pdf_bytes

    # Delete
    deleted = provider.delete(storage_key)
    assert deleted is True
    assert provider.exists(storage_key) is False


def test_s3_storage_provider_fallback_resilience():
    """Validates S3StorageProvider maintains seamless fallback and consistent interface."""
    s3_provider = S3StorageProvider(bucket_name="test-mock-bucket")
    code = "CERT-S3-001"
    sample_pdf_bytes = b"%PDF-1.4 cloud certificate content"

    # Save with resilient fallback
    storage_key = s3_provider.save_certificate(code, sample_pdf_bytes)
    assert storage_key is not None

    # Exists check
    assert s3_provider.exists(storage_key) is True

    # Bytes retrieval
    retrieved = s3_provider.get_certificate_bytes(storage_key)
    assert retrieved == sample_pdf_bytes

    # Clean up
    s3_provider.delete(storage_key)


def test_storage_singleton_factory():
    """Ensures get_storage_provider returns the configured provider instance."""
    provider = get_storage_provider()
    assert provider is not None
    assert hasattr(provider, "save_certificate")
    assert hasattr(provider, "get_certificate_bytes")
