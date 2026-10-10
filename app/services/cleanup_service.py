import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.config import settings

logger = logging.getLogger("certiflow.cleanup")


class StorageCleanupService:
    """
    Automated lifecycle management and garbage collection for temporary ZIPs and storage files.
    Mitigates DoS vulnerabilities from storage bloat.
    """

    @classmethod
    def run_retention_cleanup(cls, retention_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Scans storage directories and purges files exceeding the retention TTL.
        """
        hours = retention_hours if retention_hours is not None else settings.STORAGE_RETENTION_HOURS
        cutoff_time = time.time() - (hours * 3600)

        purged_files: List[str] = []
        total_reclaimed_bytes = 0

        target_dirs = [settings.TEMP_DIR, settings.STORAGE_DIR]

        for directory in target_dirs:
            if not directory.exists():
                continue

            for entry in directory.glob("*"):
                if entry.is_file():
                    try:
                        mtime = entry.stat().st_mtime
                        # Temp ZIP files get pruned aggressively if older than 1 hour or general retention
                        is_temp_zip = entry.suffix == ".zip" or directory == settings.TEMP_DIR
                        entry_cutoff = (time.time() - 3600) if is_temp_zip else cutoff_time

                        if mtime < entry_cutoff:
                            file_size = entry.stat().st_size
                            entry.unlink()
                            total_reclaimed_bytes += file_size
                            purged_files.append(str(entry.name))
                    except Exception as exc:
                        logger.warning(f"Error purging file {entry}: {exc}")

        logger.info(
            f"[StorageCleanup] Purged {len(purged_files)} expired files. "
            f"Reclaimed {round(total_reclaimed_bytes / (1024 * 1024), 2)} MB."
        )

        return {
            "status": "success",
            "retention_hours": hours,
            "purged_count": len(purged_files),
            "reclaimed_bytes": total_reclaimed_bytes,
            "reclaimed_mb": round(total_reclaimed_bytes / (1024 * 1024), 2),
            "purged_sample": purged_files[:10],
        }
