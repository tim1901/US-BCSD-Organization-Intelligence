from app.core.ids import research_idempotency_key
from app.storage.repositories.jobs import JobRepository

JOB_TYPES={
 'ingest_document','ingest_slack_event','backfill_slack','extract_knowledge','create_embeddings',
 'research_quick','research_standard','research_deep','brain_followup','learning_process',
 'evaluate_answer','reconcile_source','reindex_embeddings'
}

class JobService:
    def __init__(self, repo: JobRepository): self.repo=repo
    def enqueue_research(self, question: str, project_id: str | None, depth: str):
        if depth not in {'quick','standard','deep','investigative'}: raise ValueError('Invalid research depth')
        return self.repo.enqueue(f'research_{depth}', {'question':question,'project_id':project_id,'depth':depth},
                                 research_idempotency_key(question, project_id), priority=10)
