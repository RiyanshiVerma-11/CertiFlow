import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.config import settings


class SlidingWindowRateLimiter:
    """
    High-performance, thread-safe sliding window rate limiter.
    Prevents resource starvation and DoS attacks on compute-heavy endpoints.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """
        Evaluates whether the client has breached rate limit.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            # Purge timestamps older than the sliding window
            timestamps = [t for t in self.requests[client_id] if t > window_start]
            self.requests[client_id] = timestamps

            if len(timestamps) >= self.max_requests:
                earliest = timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - earliest)))
                return True, retry_after

            self.requests[client_id].append(now)
            return False, 0

    def reset(self):
        """Resets rate limiter state (useful in tests)."""
        with self.lock:
            self.requests.clear()


# Global rate limiter instance configured from app settings
global_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


def rate_limit_dependency(request: Request):
    """
    FastAPI dependency that enforces rate limits per client IP or API key.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    # Extract client identifier: X-Forwarded-For header, API key, or client IP
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_id = client_ip.split(",")[0].strip()
    elif request.client and request.client.host:
        client_id = request.client.host
    else:
        client_id = "unknown-client"

    is_limited, retry_after = global_rate_limiter.is_rate_limited(client_id)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: Maximum {global_rate_limiter.max_requests} requests per {global_rate_limiter.window_seconds} seconds. Please slow down.",
            headers={"Retry-After": str(retry_after)},
        )
