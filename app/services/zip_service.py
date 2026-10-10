import io
import zipfile
from pathlib import Path
from typing import List, Tuple
from app.config import settings


class ZipService:
    """Service to create and stream ZIP archives of generated certificates."""

    @classmethod
    def create_in_memory_zip(cls, files: List[Tuple[str, bytes]]) -> io.BytesIO:
        """
        Compresses a list of (archive_filename, file_bytes) pairs into an in-memory ZIP buffer.
        Eliminates disk bloat and avoids saving redundant zip copies on disk.
        """
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for arcname, file_bytes in files:
                zf.writestr(arcname, file_bytes)
        buffer.seek(0)
        return buffer

    @classmethod
    def create_job_zip(cls, job_id: str, files: List[Tuple[str, Path]]) -> Path:
        """
        Compresses a list of (archive_name, file_path) pairs into a temporary ZIP file.
        Returns the path to the created ZIP file.
        """
        zip_path = settings.TEMP_DIR / f"job_{job_id}_certificates.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for arcname, file_path in files:
                if file_path.exists():
                    zf.write(file_path, arcname=arcname)

        return zip_path
