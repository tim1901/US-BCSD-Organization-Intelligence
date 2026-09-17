import json, uuid
from app.storage.supabase import connection
from app.models.enums import JobStatus

class JobRepository:
    def __init__(self, organization_id: str | None = None):
        self.organization_id = organization_id

    def enqueue(self, job_type: str, payload: dict, idempotency_key: str, priority: int = 0, max_attempts: int = 5) -> str:
        job_id = str(uuid.uuid4())
        with connection(self.organization_id) as conn:
            conn.execute("""
                INSERT INTO jobs (id, job_type, payload, priority, status, available_at, attempts, max_attempts, idempotency_key, created_at)
                VALUES (%(id)s, %(type)s, %(payload)s::jsonb, %(priority)s, 'queued', NOW(), 0, %(max)s, %(key)s, NOW())
                ON CONFLICT (idempotency_key) DO NOTHING
            """ , {'id': job_id, 'type': job_type, 'payload': json.dumps(payload), 'priority': priority, 'max': max_attempts, 'key': idempotency_key})
        return job_id

    def claim_batch(self, limit: int = 10) -> list[dict]:
        with connection(self.organization_id) as conn:
            rows = conn.execute("""
                WITH picked AS (
                  SELECT id FROM jobs
                  WHERE status='queued' AND available_at <= NOW()
                  ORDER BY priority DESC, created_at ASC
                  FOR UPDATE SKIP LOCKED LIMIT %(limit)s
                )
                UPDATE jobs j
                SET status='running', locked_at=NOW(), started_at=NOW(), attempts=attempts+1
                FROM picked WHERE j.id=picked.id
                RETURNING j.*
            """, {'limit': limit}).fetchall()
        return rows

    def mark_completed(self, job_id: str):
        with connection(self.organization_id) as conn:
            conn.execute("UPDATE jobs SET status='completed', completed_at=NOW() WHERE id=%(id)s", {'id': job_id})

    def mark_retry(self, job_id: str, error_code: str, delay_seconds: int = 30):
        with connection(self.organization_id) as conn:
            conn.execute("""
              UPDATE jobs SET status=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,
              last_error=%(error)s, available_at=NOW() + (%(delay)s || ' seconds')::interval WHERE id=%(id)s
            """, {'id': job_id, 'error': error_code, 'delay': delay_seconds})
