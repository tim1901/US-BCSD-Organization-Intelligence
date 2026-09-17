from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Provenance:
    source_id: str
    source_span: str | None = None
    locator: dict[str, Any] | None = None
    evidence_role: str = 'supports'
    confidence: float | None = None

class ProvenanceService:
    def evidence_payload(self, p: Provenance) -> dict:
        return {'source_id':p.source_id,'source_span':p.source_span,'locator':p.locator or {},'evidence_role':p.evidence_role,'confidence':p.confidence}
