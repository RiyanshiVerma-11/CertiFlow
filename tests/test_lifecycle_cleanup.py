import io
import time
import zipfile
from pathlib import Path
from app.config import settings
from app.services.cleanup_service import StorageCleanupService
from app.services.zip_service import ZipService


def test_in_memory_zip_generation_zero_disk_bloat():
    """
    Validates Reason 5: In-memory streaming ZIP generation.
    Certificates are compressed into a stream without creating duplicate files on disk.
    """
    files = [
        ("Alice_CERT1.pdf", b"%PDF-1.4 Mock content 1"),
        ("Bob_CERT2.pdf", b"%PDF-1.4 Mock content 2"),
    ]

    # Generate directly into in-memory stream
    zip_buffer = ZipService.create_in_memory_zip(files)
    assert isinstance(zip_buffer, io.BytesIO)
    assert zip_buffer.getvalue().startswith(b"PK")

    # Read and verify internal structure
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        assert "Alice_CERT1.pdf" in namelist
        assert "Bob_CERT2.pdf" in namelist
        assert zf.read("Alice_CERT1.pdf") == b"%PDF-1.4 Mock content 1"


def test_storage_retention_cleanup_lifecycle(tmp_path):
    """
    Validates Reason 5: Data retention policy & automated garbage collection.
    Files older than the retention threshold are purged, reclaiming disk space.
    """
    # Create an old temporary file
    old_file = settings.TEMP_DIR / "expired_batch_test.zip"
    with open(old_file, "wb") as f:
        f.write(b"dummy zip data" * 100)

    # Set mtime to 3 hours ago
    past_mtime = time.time() - (3 * 3600)
    import os
    os.utime(old_file, (past_mtime, past_mtime))

    # Run cleanup with 1 hour retention
    report = StorageCleanupService.run_retention_cleanup(retention_hours=1)
    assert report["status"] == "success"
    assert report["purged_count"] >= 1
    assert report["reclaimed_bytes"] > 0
    assert not old_file.exists()


def test_cleanup_endpoint(client):
    """Validates the administrative maintenance cleanup endpoint."""
    res = client.post("/api/v1/jobs/cleanup")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "reclaimed_bytes" in data
