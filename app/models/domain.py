from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class NormalizedInput:
    source_type: str
    source_external_id: str | None
    title: str | None
    content: str
    source_url: str | None = None
    author: str | None = None
    occurred_at: datetime | None = None
    received_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    parent_context: dict[str, Any] = field(default_factory=dict)
    access_scope: str = 'ORGANIZATION'
    access_scope_ref: str | None = None

@dataclass(frozen=True)
class EvidenceRef:
    source_id: str
    source_span: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None

@dataclass(frozen=True)
class KnowledgeCandidate:
    knowledge_type: str
    statement: str
    truth_class: str
    confidence: float | None
    project_ref: str | None
    source_span: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class BrainPlan:
    intent: str
    project_id: str | None
    context_requirements: list[str]
    research_required: bool
    research_depth: str | None
    uncertainties: list[str]
    answer_mode: str

@dataclass(frozen=True)
class ResearchBudget:
    max_seconds: int
    max_iterations: int
    max_sources: int
    max_model_calls: int
    max_output_tokens: int
    max_cost_usd: float
