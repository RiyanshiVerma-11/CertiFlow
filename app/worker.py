"""
CertiFlow Standalone Distributed Worker
Executable command: python -m app.worker

Runs in a dedicated Docker worker container or standalone daemon process
to continuously consume bulk certificate generation tasks asynchronously
from the Redis enterprise message queue.
"""
import logging
import signal
import sys
import threading
import time

from app.config import settings
from app.database import Base, engine
from app.services.task_queue import recover_interrupted_jobs, run_redis_worker

# Ensure database tables exist upon worker startup
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("certiflow.worker")


def main():
    logger.info("=" * 60)
    logger.info("🚀 Starting CertiFlow Distributed Queue Worker")
    logger.info(f"   Task Queue Backend: {settings.TASK_QUEUE_BACKEND}")
    logger.info(f"   Redis Endpoint:     {settings.REDIS_URL}")
    logger.info("=" * 60)

    # 1. Recover any in-flight jobs interrupted during previous process crashes
    recovered = recover_interrupted_jobs()
    if recovered > 0:
        logger.info(f"[WorkerBoot] Resumed {recovered} in-flight jobs.")

    stop_event = threading.Event()

    def handle_exit(signum, frame):
        logger.info(f"Received exit signal ({signum}). Gracefully stopping worker...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    if settings.TASK_QUEUE_BACKEND.lower() in ["redis", "celery", "rq"]:
        run_redis_worker(poll_timeout=2, stop_event=stop_event)
    else:
        logger.info("[Worker] Running in durable heartbeat mode. Waiting for shutdown signal...")
        while not stop_event.is_set():
            time.sleep(1)

    logger.info("CertiFlow worker shut down cleanly.")


if __name__ == "__main__":
    main()
