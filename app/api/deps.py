import secrets
from typing import Optional
from fastapi import Request, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.config import settings
from app.services.rate_limiter import rate_limit_dependency

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Validates API key for protected bulk compute endpoints.
    If settings.API_KEY is configured, enforces authentication.
    If settings.API_KEY is empty, allows development / local evaluation mode.
    """
    configured_key = settings.API_KEY.strip()
    if not configured_key:
        # Development / evaluation mode: open access
        return "open-dev-access"

    # Also inspect Authorization: Bearer <key> if header not present
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:].strip()

    if not api_key or not secrets.compare_digest(api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: A valid API key is required via 'X-API-Key' header or 'Authorization: Bearer <token>' to access bulk endpoints.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def check_rate_limit(request: Request):
    """Dependency wrapper for sliding window rate limiting."""
    return rate_limit_dependency(request)
