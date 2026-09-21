from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.ai.embeddings import EmbeddingService
from app.ai.gemini import GeminiProvider
from app.brain.context_builder import ContextBuilder
from app.brain.gap_detection import KnowledgeGapDetector
from app.brain.planner import BrainPlanner
from app.brain.reasoning import ReasoningCore
from app.core.config import settings
from app.intelligence.search import PublicSearch
from app.memory.semantic_search import SemanticSearch
from app.models.dto import BrainCitation
from app.storage.repositories.memory import MemoryRepository
from app.storage.supabase import connection

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _public_research_query(question: str) -> str:
        return (
            "Public web research for the United States Business Council for Sustainable Development "
            "(US BCSD). Identify organizations that may compete with, overlap with, or serve as close "
            "peer organizations to US BCSD. Focus on organizations with similar mission, member value "
            "proposition, services, programs, collaboration model, or sustainability market position. "
            "For each candidate, look for evidence of overlap. Distinguish direct competitors from "
            "adjacent peers and do not imply a formal competitive relationship unless the evidence "
            "supports it. Use current public sources. User question: "
            + question
        )

    @staticmethod
    def _interaction_text(response: Any) -> str:
        """Extract final model text across current and transitional Interactions SDK shapes."""
        text = getattr(response, "output_text", None) or getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        chunks: list[str] = []
        for step in getattr(response, "steps", None) or []:
            if getattr(step, "type", None) != "model_output":
                continue
            for block in getattr(step, "content", None) or []:
                if getattr(block, "type", None) == "text":
                    value = getattr(block, "text", None)
                    if isinstance(value, str) and value.strip():
                        chunks.append(value.strip())
        return "\n".join(chunks).strip()

    @staticmethod
    def _interaction_search_evidence(response: Any) -> list[str]:
        """Capture compact search-result evidence when final model text is absent or thin."""
        evidence: list[str] = []
        for step in getattr(response, "steps", None) or []:
            if getattr(step, "type", None) != "google_search_result":
                continue
            for item in getattr(step, "result", None) or []:
                title = getattr(item, "title", None)
                url = getattr(item, "url", None)
                snippet = getattr(item, "snippet", None)
                if not snippet:
                    snippet = getattr(item, "search_suggestions", None)
                parts = [str(value).strip() for value in (title, snippet, url) if value]
                if parts:
                    evidence.append(" — ".join(parts))
        return evidence[:12]

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

        if plan.research_required:
            research_query = (
                self._public_research_query(question)
                if plan.intent == "competitive_analysis"
                else question
            )
            try:
                external_response = PublicSearch(provider).search(research_query)
                external_text = self._interaction_text(external_response)
                search_evidence = self._interaction_search_evidence(external_response)

                if external_text:
                    findings = external_text
                    if search_evidence:
                        findings += "\n\nSearch evidence:\n" + "\n".join(search_evidence)
                    memory_context["external_research"] = {
                        "type": "public_web_research",
                        "question": question,
                        "findings": findings,
                    }
                    logger.info(
                        "Public research completed intent=%s search_evidence=%s",
                        plan.intent,
                        len(search_evidence),
                    )
                elif search_evidence:
                    memory_context["external_research"] = {
                        "type": "public_web_research",
                        "question": question,
                        "findings": "\n".join(search_evidence),
                    }
                    logger.info(
                        "Public research returned search evidence without model synthesis intent=%s evidence=%s",
                        plan.intent,
                        len(search_evidence),
                    )
                else:
                    memory_context["external_research"] = {
                        "type": "public_web_research",
                        "question": question,
                        "status": "empty",
                    }
                    logger.warning("Public research returned no text or search evidence")
            except Exception as exc:
                logger.exception("Public research failed for question=%r", question)
                memory_context["external_research"] = {
                    "type": "public_web_research",
                    "question": question,
                    "status": "unavailable",
                    "error": f"{type(exc).__name__}: {exc}",
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
            answer = "I couldn't find enough information to answer that yet."

        return BrainResult(
            question=question,
            answer=answer,
            plan=plan.__dict__,
            retrieved_memory=retrieved,
            citations=self._citations(retrieved),
        )
