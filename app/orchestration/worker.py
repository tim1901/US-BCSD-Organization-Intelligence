import logging, time
from app.core.config import settings
from app.core.logging import configure_logging
from app.ingestion.slack import SlackIngestionService
from app.storage.repositories.jobs import JobRepository
from app.integrations.slack import SlackClient

logger=logging.getLogger(__name__)


def process_job(job: dict):
    job_type = job["job_type"]
    logger.info("Processing job %s type=%s", job["id"], job_type)

    if job_type in {"backfill_slack_channel", "ingest_slack_thread", "ingest_slack_event"}:
        client = SlackClient()
        service = SlackIngestionService(slack=client)
        try:
            if job_type == "backfill_slack_channel":
                count = service.backfill_channel(job)
                logger.info("Slack channel backfill queued %s thread jobs", count)
            elif job_type == "ingest_slack_thread":
                source_id = service.ingest_thread(
                    organization_id=str(job["organization_id"]),
                    workspace_id=str(job["workspace_id"]),
                    channel_id=str(job["channel_id"]),
                    thread_ts=str(job["thread_ts"]),
                )
                logger.info("Slack thread ingested source_id=%s", source_id or "message-only")
            else:
                service.ingest_event(job)
        finally:
            client.close()
        return

    # Non-Slack dispatch boundary: domain services are injected/wired here as implementation grows.
    logger.info("No handler registered for job type=%s", job_type)


def run():
    configure_logging()
    repo=JobRepository()
    logger.info("Worker started")
    while True:
        jobs=repo.claim_batch(settings.worker_batch_size)
        if not jobs:
            time.sleep(settings.worker_poll_seconds)
            continue
        for job in jobs:
            try:
                process_job(job)
                repo.mark_completed(job["id"])
            except Exception:
                logger.exception("Job failed: %s", job["id"])
                repo.mark_retry(job["id"], "processing_error")


if __name__=="__main__":
    run()
