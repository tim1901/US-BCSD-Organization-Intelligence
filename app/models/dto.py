from pydantic import BaseModel, Field
from typing import Any


class HealthResponse(BaseModel):
    status: str
    dependencies: dict[str, str] | None = None


class IngestTextRequest(BaseModel):
    title: str | None = None
    content: str = Field(min_length=1)
    source_type: str = 'manual_text'
    project_id: str | None = None
    access_scope: str = 'ORGANIZATION'


class BrainAskRequest(BaseModel):
    question: str = Field(min_length=1)
    project_id: str | None = None
    conversation_id: str | None = None
    channel_id: str | None = None


class BrainCitation(BaseModel):
    source_id: str | None = None
    source_title: str | None = None
    source_span: str | None = None
    similarity: float
    object_type: str
    object_id: str


class BrainAskResponse(BaseModel):
    question: str
    answer: str
    plan: dict[str, Any]
    retrieved_memory: list[dict[str, Any]]
    citations: list[BrainCitation]


class ResearchStartRequest(BaseModel):
    question: str = Field(min_length=1)
    project_id: str | None = None
    depth: str = 'standard'


class FeedbackRequest(BaseModel):
    conversation_id: str | None = None
    message_id: str | None = None
    feedback_type: str
    feedback_text: str | None = None
    related_object_type: str | None = None
    related_object_id: str | None = None


class JobResponse(BaseModel):
    job_id: str
    status: str


class BrainPlanResponse(BaseModel):
    intent: str
    project_id: str | None
    context_requirements: list[str]
    research_required: bool
    research_depth: str | None
    uncertainties: list[str]
    answer_mode: str
