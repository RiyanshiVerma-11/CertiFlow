import pytest
from app.config import settings
from app.services.rate_limiter import SlidingWindowRateLimiter, global_rate_limiter


def test_sliding_window_rate_limiter_logic():
    """Validates the sliding window token rate limiter under rapid bursts."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10)
    client_ip = "192.168.1.100"

    # 3 requests should pass
    assert limiter.is_rate_limited(client_ip)[0] is False
    assert limiter.is_rate_limited(client_ip)[0] is False
    assert limiter.is_rate_limited(client_ip)[0] is False

    # 4th request within window must be rate-limited
    is_limited, retry_after = limiter.is_rate_limited(client_ip)
    assert is_limited is True
    assert retry_after > 0


def test_endpoint_rate_limiting_returns_429(client):
    """
    Validates that client receives HTTP 429 Too Many Requests when rate limit is exceeded.
    """
    # Temporarily set tight limit for testing
    original_max = global_rate_limiter.max_requests
    global_rate_limiter.max_requests = 2
    global_rate_limiter.reset()

    payload = {
        "title": "Rate Limit Test",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [{"name": "User", "email": "user@example.com"}],
    }

    try:
        # Request 1 & 2 should succeed
        r1 = client.post("/api/v1/jobs", json=payload)
        assert r1.status_code == 202

        r2 = client.post("/api/v1/jobs", json=payload)
        assert r2.status_code == 202

        # Request 3 must return HTTP 429
        r3 = client.post("/api/v1/jobs", json=payload)
        assert r3.status_code == 429
        assert "Retry-After" in r3.headers
        assert "rate limit exceeded" in r3.json()["detail"].lower()

    finally:
        # Restore configuration
        global_rate_limiter.max_requests = original_max
        global_rate_limiter.reset()


def test_api_key_authentication_enforcement(client):
    """
    Validates Reason 6 API key security when an API key is configured.
    """
    original_key = settings.API_KEY
    settings.API_KEY = "test-secret-enterprise-key-12345"

    payload = {
        "title": "Auth Guard Test",
        "issuer_name": "Aereo Academy",
        "issue_date": "2026-10-07",
        "recipients": [{"name": "User", "email": "user@example.com"}],
    }

    try:
        # 1. Missing API Key returns 401 Unauthorized
        res_no_key = client.post("/api/v1/jobs", json=payload)
        assert res_no_key.status_code == 401

        # 2. Invalid API Key returns 401 Unauthorized
        res_bad_key = client.post(
            "/api/v1/jobs", json=payload, headers={"X-API-Key": "wrong-key"}
        )
        assert res_bad_key.status_code == 401

        # 3. Valid API Key via X-API-Key header succeeds
        res_valid = client.post(
            "/api/v1/jobs", json=payload, headers={"X-API-Key": "test-secret-enterprise-key-12345"}
        )
        assert res_valid.status_code == 202

        # 4. Valid API Key via Authorization: Bearer header succeeds
        res_bearer = client.post(
            "/api/v1/jobs",
            json=payload,
            headers={"Authorization": "Bearer test-secret-enterprise-key-12345"},
        )
        assert res_bearer.status_code == 202

    finally:
        settings.API_KEY = original_key


def test_verify_certificate_rate_limiting_brute_force_protection(client):
    """
    Validates Reason 6: The public verification endpoint is protected against
    brute-force code guessing attacks via SlidingWindowRateLimiter.
    """
    original_max = global_rate_limiter.max_requests
    global_rate_limiter.max_requests = 3
    global_rate_limiter.reset()

    try:
        # First 3 verification attempts should succeed (returning 200 with is_valid=False)
        r1 = client.get("/api/v1/certificates/verify/RANDOM-CODE-1")
        assert r1.status_code == 200
        assert r1.json()["is_valid"] is False

        r2 = client.get("/api/v1/certificates/verify/RANDOM-CODE-2")
        assert r2.status_code == 200

        r3 = client.get("/api/v1/certificates/verify/RANDOM-CODE-3")
        assert r3.status_code == 200

        # 4th brute-force attempt must trigger 429 Too Many Requests
        r4 = client.get("/api/v1/certificates/verify/RANDOM-CODE-4")
        assert r4.status_code == 429
        assert "Retry-After" in r4.headers
        assert "rate limit exceeded" in r4.json()["detail"].lower()

    finally:
        global_rate_limiter.max_requests = original_max
        global_rate_limiter.reset()

