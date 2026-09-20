from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.embeddings import EmbeddingService
from app.ai.gemini import GeminiProvider
from app.brain.context_builder import ContextBuilder
from app.brain.gap_detection import KnowledgeGapDetector
from app.brain.planner import BrainPlanner
from app.brain.reasoning import ReasoningCore
from app.core.config import settings
from app.models.dto import BrainAskRequest, BrainAskResponse, BrainCitation
from app.memory.semantic_search import SemanticSearch
from app.storage.repositories.memory import MemoryRepository
from app.storage.supabase import connection

router = APIRouter(prefix="/api/brain", tags=["brain"])


def _get_organization_id() -> str:
    with connection() as conn:
        row = conn.execute(
            "SELECT id FROM organizations WHERE slug = %s LIMIT 1",
            ("us-bcsd",),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=503, detail="US BCSD organization is not configured")
    return str(row["id"])


def _citation_rows(rows: list[dict]) -> list[BrainCitation]:
    citations: list[BrainCitation] = []
    seen: set[tuple[str | None, str | None]] = set()
    for row in rows:
        key = (row.get("source_id"), row.get("source_span"))
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            BrainCitation(
                source_id=str(row["source_id"]) if row.get("source_id") else None,
                source_title=row.get("source_title"),
                source_span=row.get("source_span"),
                similarity=float(row["similarity"]),
                object_type=str(row["object_type"]),
                object_id=str(row["object_id"]),
            )
        )
    return citations


@router.post("/ask", response_model=BrainAskResponse)
def ask(request: BrainAskRequest):
    plan = BrainPlanner().plan(request.question, request.project_id)
    organization_id = _get_organization_id()

    provider = GeminiProvider()
    embedding = EmbeddingService(provider=provider).embed(request.question)
    retrieved = SemanticSearch(organization_id).search(
        embedding,
        limit=settings.memory_retrieval_limit,
        min_similarity=settings.memory_min_similarity,
    )

    memory_context: dict = {
        "semantic_results": retrieved,
        "result_count": len(retrieved),
    }

    if request.project_id:
        repository = MemoryRepository(organization_id)
        memory_context["project"] = repository.get_project(request.project_id)
        memory_context["decisions"] = repository.get_decisions(request.project_id)
        memory_context["open_questions"] = repository.get_open_questions(request.project_id)

    context = ContextBuilder().build(
        question=request.question,
        memory_context=memory_context,
        conversation_context={
            "conversation_id": request.conversation_id,
        } if request.conversation_id else None,
    )
    context["plan"] = plan.__dict__
    context["knowledge_gaps"] = KnowledgeGapDetector().detect(plan, context)

    answer = ReasoningCore(provider).answer(context)

    if not answer:
        answer = "The available organizational memory did not produce an answer."

    return BrainAskResponse(
        question=request.question,
        answer=answer,
        plan=plan.__dict__,
        retrieved_memory=retrieved,
        citations=_citation_rows(retrieved),
    )
