import zipfile
from pathlib import Path
from typing import List, Tuple
from app.config import settings


class ZipService:
    """Service to create and stream ZIP archives of generated certificates."""

    @classmethod
    def create_job_zip(cls, job_id: str, files: List[Tuple[str, Path]]) -> Path:
        """
        Compresses a list of (archive_name, file_path) pairs into a ZIP file.
        Returns the path to the created ZIP file.
        """
        zip_path = settings.TEMP_DIR / f"job_{job_id}_certificates.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for arcname, file_path in files:
                if file_path.exists():
                    zf.write(file_path, arcname=arcname)

        return zip_path
