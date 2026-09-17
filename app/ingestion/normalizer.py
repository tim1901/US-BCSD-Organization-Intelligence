from datetime import datetime, timezone
from app.models.domain import NormalizedInput

def normalize_text(content: str, *, source_type: str, title: str | None = None,
                   source_external_id: str | None = None, source_url: str | None = None,
                   project_id: str | None = None, access_scope: str = 'ORGANIZATION') -> NormalizedInput:
    return NormalizedInput(source_type=source_type, source_external_id=source_external_id,
                           title=title, content=content.strip(), source_url=source_url,
                           received_at=datetime.now(timezone.utc),
                           metadata={'project_id': project_id} if project_id else {},
                           access_scope=access_scope,
                           access_scope_ref=project_id)
