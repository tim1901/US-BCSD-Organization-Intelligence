import logging
import re
import time

from app.brain.service import BrainService
from app.core.config import settings
from app.core.logging import configure_logging
from app.ingestion.slack import SlackIngestionService
from app.integrations.slack import SlackClient
from app.storage.repositories.jobs import JobRepository

logger = logging.getLogger(__name__)


def _format_slack_brain_response(answer: str, citations: list) -> str:
    """Keep Slack replies conversational and free of AI-style formatting or source dumps."""
    text = (answer or "").strip()

    # The conversational prompt should normally prevent this, but normalize common
    # Markdown artifacts defensively before sending the message to Slack.
    text = re.sub(r"(?im)^\s*#{1,6}\s*", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*[-*•]\s+", "", text)

    # Do not expose provenance/source sections in the conversational Slack interface.
    text = re.split(r"(?im)^\s*(?:sources|citations|evidence)\s*:??\s*$", text, maxsplit=1)[0].rstrip()

    return text


def process_job(job: dict):
    job_type = job["job_type"]
    payload = job.get("payload") or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Job payload must be an object, got {type(payload).__name__}")
    job_data = {**job, **payload}
    logger.info("Processing job %s type=%s", job["id"], job_type)

    if job_type in {"backfill_slack_channel", "ingest_slack_thread", "ingest_slack_event"}:
        client = SlackClient()
        service = SlackIngestionService(slack=client)
        try:
            if job_type == "backfill_slack_channel":
                count = service.backfill_channel(job_data)
                logger.info("Slack channel backfill queued %s thread jobs", count)
            elif job_type == "ingest_slack_thread":
                source_id = service.ingest_thread(
                    organization_id=str(job_data["organization_id"]),
                    workspace_id=str(job_data["workspace_id"]),
                    channel_id=str(job_data["channel_id"]),
                    thread_ts=str(job_data["thread_ts"]),
                )
                logger.info("Slack thread ingested source_id=%s", source_id or "message-only")
            else:
                service.ingest_event(job_data)
        finally:
            client.close()
        return

    if job_type == "slack_brain_command":
        organization_id = str(job_data["organization_id"])
        result = BrainService(organization_id).ask(
            question=str(job_data["question"]),
            channel_id=str(job_data["channel_id"]),
            conversation_context={
                "interface": "slack",
                "workspace_id": str(job_data.get("workspace_id") or ""),
                "channel_id": str(job_data["channel_id"]),
                "channel_name": str(job_data.get("channel_name") or ""),
                "user_id": str(job_data.get("user_id") or ""),
            },
        )
        response_text = _format_slack_brain_response(result.answer, result.citations)
        try:
            SlackClient.post_response_url(str(job_data["response_url"]), response_text)
        except Exception:
            logger.exception("Failed to send Slack Brain response for job %s", job["id"])
            raise
        return

    logger.info("No handler registered for job type=%s", job_type)


def run():
    configure_logging()
    repo = JobRepository()
    logger.info("Worker started")
    while True:
        jobs = repo.claim_batch(settings.worker_batch_size)
        if not jobs:
            time.sleep(settings.worker_poll_seconds)
            continue
        for job in jobs:
            try:
                process_job(job)
                repo.mark_completed(job["id"])
            except Exception as exc:
                logger.exception("Job failed: %s", job["id"])
                detail = f"{type(exc).__name__}: {exc}".strip()
                repo.mark_retry(job["id"], detail[:1000])


if __name__ == "__main__":
    run()
