import hashlib
import uuid

def new_id() -> str:
    return str(uuid.uuid4())

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def research_idempotency_key(question: str, project_id: str | None) -> str:
    digest = sha256_text(' '.join(question.lower().split()))
    return f'research:{digest}:{project_id or "none"}'
