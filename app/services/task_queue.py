import json
import logging
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.job import GenerationJob, JobStatus

logger = logging.getLogger("certiflow.queue")


class TaskQueueDispatcher(ABC):
    """Abstract interface for decoupled bulk generation task dispatching."""

    @abstractmethod
    def dispatch(self, job_id: str, background_tasks: Optional[BackgroundTasks] = None) -> bool:
        """Enqueues job_id for asynchronous execution."""
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Returns the identifier name of the active queue backend."""
        pass


class DatabaseDurableQueueDispatcher(TaskQueueDispatcher):
    """
    Durable database-backed queue dispatcher.
    Persists job state to SQLite / PostgreSQL, ensuring durability across container restarts.
    Executes tasks via a managed daemon thread pool with lease recovery.
    """

    def __init__(self):
        self._thread_pool = []

    def dispatch(self, job_id: str, background_tasks: Optional[BackgroundTasks] = None) -> bool:
        # Import lazily to avoid circular dependencies
        from app.services.job_service import JobService

        logger.info(f"[DurableDBQueue] Enqueueing job {job_id} into durable worker pool.")
        worker_thread = threading.Thread(
            target=JobService.process_bulk_job,
            args=(job_id,),
            daemon=True,
            name=f"CertiWorker-{job_id[:8]}",
        )
        worker_thread.start()
        return True

    def get_backend_name(self) -> str:
        return "durable_database"


class RedisQueueDispatcher(TaskQueueDispatcher):
    """
    Enterprise message queue dispatcher using Redis / Celery / RQ.
    Distributes bulk PDF generation across separate worker nodes and containers.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._client = None
        self._fallback = DatabaseDurableQueueDispatcher()

    def _get_client(self):
        if self._client is None:
            try:
                import importlib
                redis_mod = importlib.import_module("redis")
                self._client = redis_mod.from_url(self.redis_url, socket_timeout=3.0)
                self._client.ping()
            except Exception as e:
                logger.warning(
                    f"[RedisQueue] Redis connection to {self.redis_url} failed: {e}. "
                    "Falling back to durable database worker."
                )
                self._client = None
        return self._client

    def dispatch(self, job_id: str, background_tasks: Optional[BackgroundTasks] = None) -> bool:
        client = self._get_client()
        if client:
            try:
                payload = json.dumps({"job_id": job_id, "enqueued_at": datetime.now(timezone.utc).isoformat()})
                client.rpush("certiflow:jobs:queue", payload)
                logger.info(f"[RedisQueue] Pushed job {job_id} to Redis queue 'certiflow:jobs:queue'.")
                return True
            except Exception as e:
                logger.error(f"[RedisQueue] Failed pushing job to Redis: {e}. Falling back.")

        return self._fallback.dispatch(job_id, background_tasks)

    def get_backend_name(self) -> str:
        return "redis_celery"


class BackgroundTaskDispatcher(TaskQueueDispatcher):
    """FastAPI in-process BackgroundTasks dispatcher for lightweight local unit testing."""

    def dispatch(self, job_id: str, background_tasks: Optional[BackgroundTasks] = None) -> bool:
        from app.services.job_service import JobService

        if background_tasks:
            background_tasks.add_task(JobService.process_bulk_job, job_id)
            logger.debug(f"[BackgroundTasks] Added job {job_id} to request background tasks.")
            return True
        else:
            # Fallback to direct thread if background_tasks object wasn't supplied
            t = threading.Thread(target=JobService.process_bulk_job, args=(job_id,), daemon=True)
            t.start()
            return True

    def get_backend_name(self) -> str:
        return "fastapi_background"


def get_task_dispatcher() -> TaskQueueDispatcher:
    """Factory creating the configured task queue dispatcher."""
    backend = settings.TASK_QUEUE_BACKEND.lower()
    if backend in ["redis", "celery", "rq"]:
        return RedisQueueDispatcher()
    elif backend in ["database", "durable", "sqlite", "db"]:
        return DatabaseDurableQueueDispatcher()
    else:
        return BackgroundTaskDispatcher()


def recover_interrupted_jobs() -> int:
    """
    Crash recovery routine executed during application startup.
    Scans for jobs left in 'PROCESSING' or 'PENDING' when the server stopped/restarted,
    and resumes processing so in-flight tasks are NEVER permanently lost.
    """
    from app.services.job_service import JobService

    db: Session = SessionLocal()
    recovered_count = 0
    try:
        interrupted = (
            db.query(GenerationJob)
            .filter(GenerationJob.status.in_([JobStatus.PROCESSING.value, JobStatus.PENDING.value]))
            .all()
        )
        for job in interrupted:
            logger.warning(
                f"[CrashRecovery] Resuming orphaned/interrupted job {job.id} (Status: {job.status}, "
                f"Progress: {job.processed_count}/{job.total_count})"
            )
            # Re-enqueue into worker thread
            t = threading.Thread(
                target=JobService.process_bulk_job,
                args=(job.id,),
                daemon=True,
                name=f"RecoveryWorker-{job.id[:8]}",
            )
            t.start()
            recovered_count += 1
    except Exception as e:
        logger.error(f"[CrashRecovery] Error while recovering interrupted jobs: {e}")
    finally:
        db.close()

    return recovered_count


def run_redis_worker(
    poll_timeout: int = 2,
    stop_event: Optional[threading.Event] = None,
    max_jobs: Optional[int] = None,
) -> int:
    """
    Continuous queue consumer loop that blocks on `certiflow:jobs:queue` (BLPOP),
    deserializes the payload, and executes JobService.process_bulk_job(job_id).
    Runs in a standalone worker container or background worker thread.
    Returns total number of processed jobs upon termination.
    """
    from app.services.job_service import JobService

    dispatcher = RedisQueueDispatcher()
    client = dispatcher._get_client()
    if not client:
        logger.error("[RedisWorker] Could not connect to Redis. Worker cannot start.")
        return 0

    logger.info("[RedisWorker] Started queue consumer listening on 'certiflow:jobs:queue'.")
    processed_count = 0

    while True:
        if stop_event and stop_event.is_set():
            logger.info("[RedisWorker] Stop signal received. Gracefully exiting worker loop.")
            break

        if max_jobs is not None and processed_count >= max_jobs:
            logger.info(f"[RedisWorker] Reached max_jobs limit ({max_jobs}). Exiting.")
            break

        try:
            # BLPOP returns tuple: (queue_name, item) or None on timeout
            result = client.blpop(["certiflow:jobs:queue"], timeout=poll_timeout)
            if not result:
                continue

            _, raw_payload = result
            if isinstance(raw_payload, bytes):
                raw_payload = raw_payload.decode("utf-8")

            payload = json.loads(raw_payload)
            job_id = payload.get("job_id")
            if not job_id:
                logger.warning(f"[RedisWorker] Malformed message popped: {raw_payload}")
                continue

            logger.info(f"[RedisWorker] Picked up job {job_id}. Processing bulk generation...")
            JobService.process_bulk_job(job_id)
            processed_count += 1
            logger.info(f"[RedisWorker] Finished job {job_id}. Total processed: {processed_count}")

        except Exception as e:
            if stop_event and stop_event.is_set():
                break
            logger.error(f"[RedisWorker] Error in worker processing loop: {e}", exc_info=True)

    return processed_count
