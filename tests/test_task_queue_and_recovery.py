import uuid
from datetime import datetime, timezone
from app.models.job import GenerationJob, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.services.task_queue import (
    get_task_dispatcher,
    DatabaseDurableQueueDispatcher,
    BackgroundTaskDispatcher,
    recover_interrupted_jobs,
)
from app.services.job_service import JobService


def test_task_queue_dispatcher_backends():
    """Validates Reason 2: Task queue abstraction across multiple backends."""
    db_dispatcher = DatabaseDurableQueueDispatcher()
    assert db_dispatcher.get_backend_name() == "durable_database"

    bg_dispatcher = BackgroundTaskDispatcher()
    assert bg_dispatcher.get_backend_name() == "fastapi_background"

    active_dispatcher = get_task_dispatcher()
    assert active_dispatcher is not None


def test_crash_recovery_resumes_interrupted_jobs(db_session):
    """
    Validates Reason 2: Crash resilience & orphan job recovery.
    Simulates a server process that crashed while a job was in 'PROCESSING' state.
    On application startup, recover_interrupted_jobs() detects and resumes the orphaned job.
    """
    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        title="Interrupted Flight Certification",
        issuer_name="Aereo Defense",
        issue_date="2026-10-07",
        status=JobStatus.PROCESSING.value,
        total_count=1,
        processed_count=0,
        success_count=0,
        failed_count=0,
    )
    db_session.add(job)

    cert = Certificate(
        id=str(uuid.uuid4()),
        job_id=job_id,
        recipient_name="Captain Marvel",
        recipient_email="captain@marvel.com",
        certificate_code=f"CERT-{uuid.uuid4().hex[:8].upper()}",
        status=CertificateStatus.PENDING.value,
    )
    db_session.add(cert)
    db_session.commit()

    # Trigger recovery routine (simulates server restart lifespan)
    recovered = recover_interrupted_jobs()
    assert recovered >= 1


def test_redis_worker_queue_processing():
    """
    Validates Reason 4: RedisQueueDispatcher and run_redis_worker consumer loop.
    Simulates enqueuing a job to Redis and consuming it via the standalone worker.
    """
    from unittest.mock import MagicMock, patch
    import json
    from app.services.task_queue import RedisQueueDispatcher, run_redis_worker

    fake_redis = MagicMock()
    fake_queue = [json.dumps({"job_id": "job-test-redis-123"}).encode("utf-8")]

    def fake_blpop(keys, timeout=0):
        if fake_queue:
            return ("certiflow:jobs:queue", fake_queue.pop(0))
        return None

    fake_redis.blpop.side_effect = fake_blpop

    with patch.object(RedisQueueDispatcher, "_get_client", return_value=fake_redis), \
         patch("app.services.job_service.JobService.process_bulk_job") as mock_process:

        processed = run_redis_worker(poll_timeout=1, max_jobs=1)
        assert processed == 1
        mock_process.assert_called_once_with("job-test-redis-123")
