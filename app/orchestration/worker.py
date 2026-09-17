import logging, time
from app.core.config import settings
from app.core.logging import configure_logging
from app.storage.repositories.jobs import JobRepository

logger=logging.getLogger(__name__)

def process_job(job: dict):
    # Dispatch boundary: domain services are injected/wired here as implementation grows.
    logger.info('Processing job %s type=%s', job['id'], job['job_type'])

def run():
    configure_logging(); repo=JobRepository()
    logger.info('Worker started')
    while True:
        jobs=repo.claim_batch(settings.worker_batch_size)
        if not jobs:
            time.sleep(settings.worker_poll_seconds); continue
        for job in jobs:
            try:
                process_job(job); repo.mark_completed(job['id'])
            except Exception:
                logger.exception('Job failed: %s', job['id']); repo.mark_retry(job['id'],'processing_error')

if __name__=='__main__': run()
