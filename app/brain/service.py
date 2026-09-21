from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ai.embeddings import EmbeddingService
from app.ai.gemini import GeminiProvider
from app.brain.context_builder import ContextBuilder
from app.brain.gap_detection import KnowledgeGapDetector
from app.brain.planner import BrainPlanner
from app.brain.reasoning import ReasoningCore
from app.core.config import settings
from app.memory.semantic_search import SemanticSearch
from app.models.dto import BrainCitation
from app.storage.repositories.memory import MemoryRepository
from app.storage.supabase import connection


@dataclass
class BrainResult:
    question: str
    answer: str
    plan: dict[str, Any]
    retrieved_memory: list[dict[str, Any]]
    citations: list[BrainCitation]


class BrainService:
    """Canonical application service used by HTTP and Slack Brain interfaces."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    @staticmethod
    def organization_id_for_us_bcsd() -> str:
        with connection() as conn:
            row = conn.execute(
                "SELECT id FROM organizations WHERE slug = %s LIMIT 1",
                ("us-bcsd",),
            ).fetchone()
        if not row:
            raise RuntimeError("US BCSD organization is not configured")
        return str(row["id"])

    @staticmethod
    def _citations(rows: list[dict]) -> list[BrainCitation]:
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

    def ask(
        self,
        *,
        question: str,
        project_id: str | None = None,
        conversation_id: str | None = None,
        channel_id: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> BrainResult:
        plan = BrainPlanner().plan(question, project_id)

        provider = GeminiProvider()
        embedding = EmbeddingService(provider=provider).embed(question)
        retrieved = SemanticSearch(self.organization_id).search(
            embedding,
            limit=settings.memory_retrieval_limit,
            min_similarity=settings.memory_min_similarity,
            channel_id=channel_id,
        )

        memory_context: dict[str, Any] = {
            "semantic_results": retrieved,
            "result_count": len(retrieved),
        }

        if project_id:
            repository = MemoryRepository(self.organization_id)
            memory_context["project"] = repository.get_project(project_id)
            memory_context["decisions"] = repository.get_decisions(project_id)
            memory_context["open_questions"] = repository.get_open_questions(project_id)

        context = ContextBuilder().build(
            question=question,
            memory_context=memory_context,
            conversation_context={
                "conversation_id": conversation_id,
                **(conversation_context or {}),
            },
        )
        context["plan"] = plan.__dict__
        context["knowledge_gaps"] = KnowledgeGapDetector().detect(plan, context)

        answer = ReasoningCore(provider).answer(context)
        if not answer:
            answer = "The available organizational memory did not produce an answer."

        return BrainResult(
            question=question,
            answer=answer,
            plan=plan.__dict__,
            retrieved_memory=retrieved,
            citations=self._citations(retrieved),
        )
