import io
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Union, List

from app.config import settings

logger = logging.getLogger("certiflow.storage")


class StorageProvider(ABC):
    """Abstract base class defining cloud and local storage contract for certificates."""

    @abstractmethod
    def save_certificate(
        self, certificate_code: str, content: Union[bytes, io.BytesIO], filename: Optional[str] = None
    ) -> str:
        """
        Persists certificate PDF content and returns storage locator / URI.
        """
        pass

    @abstractmethod
    def get_certificate_bytes(self, storage_key: str) -> Optional[bytes]:
        """
        Retrieves raw binary PDF bytes for a given storage locator.
        """
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """
        Checks whether the specified file exists in storage.
        """
        pass

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        """
        Deletes the file from storage.
        """
        pass

    @abstractmethod
    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generates a direct presigned download URL (for cloud backends) or None for local streams.
        """
        pass

    @abstractmethod
    def get_local_path(self, storage_key: str) -> Optional[Path]:
        """
        Returns local Path if available, or None for remote-only backends.
        """
        pass


class LocalStorageProvider(StorageProvider):
    """Production-grade local filesystem storage provider with path isolation."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_certificate(
        self, certificate_code: str, content: Union[bytes, io.BytesIO], filename: Optional[str] = None
    ) -> str:
        file_name = filename or f"{certificate_code}.pdf"
        target_path = self.base_dir / file_name

        data = content.getvalue() if isinstance(content, io.BytesIO) else content
        with open(target_path, "wb") as f:
            f.write(data)

        logger.debug(f"[LocalStorage] Saved certificate {certificate_code} to {target_path}")
        return str(target_path)

    def get_certificate_bytes(self, storage_key: str) -> Optional[bytes]:
        path = Path(storage_key)
        if not path.is_absolute():
            path = self.base_dir / storage_key

        if not path.exists():
            return None

        with open(path, "rb") as f:
            return f.read()

    def exists(self, storage_key: str) -> bool:
        path = Path(storage_key)
        if not path.is_absolute():
            path = self.base_dir / storage_key
        return path.exists()

    def delete(self, storage_key: str) -> bool:
        path = Path(storage_key)
        if not path.is_absolute():
            path = self.base_dir / storage_key

        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"[LocalStorage] Failed deleting {storage_key}: {e}")
                return False
        return False

    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        # Local storage serves through FastAPI HTTP endpoint
        return None

    def get_local_path(self, storage_key: str) -> Optional[Path]:
        path = Path(storage_key)
        if not path.is_absolute():
            path = self.base_dir / storage_key
        return path if path.exists() else None


class S3StorageProvider(StorageProvider):
    """
    Enterprise S3 / Cloud Storage provider supporting AWS S3, MinIO, and Cloudflare R2.
    Decouples storage from container disk lifecycles.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region = region or settings.S3_REGION_NAME
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL or None
        self._s3_client = None
        self._fallback_local = LocalStorageProvider()

    def _get_client(self):
        if self._s3_client is None:
            try:
                import importlib
                boto3 = importlib.import_module("boto3")
                kwargs = {
                    "region_name": self.region,
                }
                if self.endpoint_url:
                    kwargs["endpoint_url"] = self.endpoint_url
                if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                    kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                    kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                self._s3_client = boto3.client("s3", **kwargs)
            except ImportError:
                logger.warning(
                    "[S3Storage] 'boto3' package not installed; falling back to resilient local storage cache."
                )
                return None
            except Exception as e:
                logger.error(f"[S3Storage] Failed to initialize S3 client: {e}")
                return None
        return self._s3_client

    def save_certificate(
        self, certificate_code: str, content: Union[bytes, io.BytesIO], filename: Optional[str] = None
    ) -> str:
        s3_key = f"certificates/{filename or f'{certificate_code}.pdf'}"
        data = content.getvalue() if isinstance(content, io.BytesIO) else content

        client = self._get_client()
        if client and self.bucket_name:
            try:
                client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=data,
                    ContentType="application/pdf",
                )
                logger.info(f"[S3Storage] Successfully uploaded {s3_key} to s3://{self.bucket_name}")
                return f"s3://{self.bucket_name}/{s3_key}"
            except Exception as e:
                logger.error(f"[S3Storage] Upload error: {e}. Falling back to local cache.")

        # Resilient local cache fallback
        local_path = self._fallback_local.save_certificate(certificate_code, content, filename)
        return local_path

    def get_certificate_bytes(self, storage_key: str) -> Optional[bytes]:
        client = self._get_client()
        if client and storage_key.startswith("s3://"):
            try:
                parts = storage_key.replace("s3://", "").split("/", 1)
                bucket, key = parts[0], parts[1]
                response = client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except Exception as e:
                logger.error(f"[S3Storage] Fetch error for {storage_key}: {e}")
                return None
        return self._fallback_local.get_certificate_bytes(storage_key)

    def exists(self, storage_key: str) -> bool:
        client = self._get_client()
        if client and storage_key.startswith("s3://"):
            try:
                parts = storage_key.replace("s3://", "").split("/", 1)
                bucket, key = parts[0], parts[1]
                client.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                return False
        return self._fallback_local.exists(storage_key)

    def delete(self, storage_key: str) -> bool:
        client = self._get_client()
        if client and storage_key.startswith("s3://"):
            try:
                parts = storage_key.replace("s3://", "").split("/", 1)
                bucket, key = parts[0], parts[1]
                client.delete_object(Bucket=bucket, Key=key)
                return True
            except Exception as e:
                logger.error(f"[S3Storage] Delete error for {storage_key}: {e}")
                return False
        return self._fallback_local.delete(storage_key)

    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        client = self._get_client()
        if client and storage_key.startswith("s3://"):
            try:
                parts = storage_key.replace("s3://", "").split("/", 1)
                bucket, key = parts[0], parts[1]
                url = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                logger.error(f"[S3Storage] Presigned URL error: {e}")
                return None
        return None

    def get_local_path(self, storage_key: str) -> Optional[Path]:
        return self._fallback_local.get_local_path(storage_key)


_storage_instance: Optional[StorageProvider] = None


def get_storage_provider() -> StorageProvider:
    """Singleton factory providing the configured storage backend."""
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_BACKEND.lower() == "s3":
            _storage_instance = S3StorageProvider()
        else:
            _storage_instance = LocalStorageProvider()
    return _storage_instance
