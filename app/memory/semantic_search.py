from __future__ import annotations

from app.storage.supabase import connection


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(format(float(value), ".9g") for value in values) + "]"


class SemanticSearch:
    """Organization-scoped pgvector retrieval with provenance and optional Slack channel scoping."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def search(
        self,
        embedding: list[float],
        *,
        limit: int = 10,
        min_similarity: float = 0.0,
        channel_id: str | None = None,
    ) -> list[dict]:
        vector = _vector_literal(embedding)
        with connection(self.organization_id) as conn:
            return conn.execute(
                """
                SELECT
                    e.id,
                    e.object_type,
                    e.object_id,
                    e.chunk_text,
                    1 - (e.embedding <=> %(embedding)s::vector) AS similarity,
                    COALESCE(k.source_id, ss.id) AS source_id,
                    COALESCE(sk.title, ss.title) AS source_title,
                    COALESCE(k.source_span, sc.source_span) AS source_span,
                    k.knowledge_type,
                    k.truth_class,
                    k.confidence
                FROM embeddings e
                LEFT JOIN knowledge_items k
                  ON e.object_type = 'knowledge_item'
                 AND e.object_id = k.id
                LEFT JOIN sources sk
                  ON k.source_id = sk.id
                LEFT JOIN source_chunks sc
                  ON e.object_type = 'source_chunk'
                 AND e.object_id = sc.id
                LEFT JOIN source_documents sd
                  ON sc.source_document_id = sd.id
                LEFT JOIN sources ss
                  ON sd.source_id = ss.id
                WHERE e.organization_id = %(organization_id)s
                  AND e.object_type IN ('knowledge_item', 'source_chunk')
                  AND 1 - (e.embedding <=> %(embedding)s::vector) >= %(min_similarity)s
                  AND (
                      %(channel_id)s::text IS NULL
                      OR COALESCE(
                          sk.metadata ->> 'channel_id',
                          ss.metadata ->> 'channel_id'
                      ) = %(channel_id)s::text
                  )
                ORDER BY e.embedding <=> %(embedding)s::vector
                LIMIT %(limit)s
                """,
                {
                    "embedding": vector,
                    "organization_id": self.organization_id,
                    "min_similarity": min_similarity,
                    "channel_id": channel_id,
                    "limit": limit,
                },
            ).fetchall()
