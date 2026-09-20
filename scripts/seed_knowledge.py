"""Seed the canonical US BCSD organizational memory from the checked-in seed source.

This script is intentionally idempotent. The seed source is registered with provenance,
extracted into structured knowledge with Gemini, chunked, embedded, and written to
PostgreSQL/pgvector. Gemini organizational calls remain stateless (store=False); the
database is the canonical memory.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.ai.embeddings import EmbeddingService
from app.ai.gemini import GeminiProvider
from app.ai.schemas.extraction import ExtractionSchema
from app.core.config import settings
from app.core.ids import sha256_text
from app.ingestion.extractors import KnowledgeExtractor
from app.ingestion.normalizer import normalize_text
from app.storage.supabase import close_pool, connection


REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = REPO_ROOT / "knowledge" / "seed" / "us_bcsd_seed_knowledge.md"
ORGANIZATION_SLUG = "us-bcsd"
PARSER_VERSION = "seed-markdown-v1"
EMBEDDING_VERSION = "gemini-embedding-v1"


def _chunk_markdown(content: str) -> list[tuple[str, str]]:
    """Create deterministic section chunks while preserving headings as provenance spans."""
    chunks: list[tuple[str, str]] = []
    current_heading = "document"
    current_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_lines:
                chunks.append(("\\n".join(current_lines).strip(), current_heading))
                current_lines = []
            current_heading = re.sub(r"^#+\\s*", "", stripped).strip() or "heading"
        elif stripped:
            current_lines.append(stripped)

    if current_lines:
        chunks.append(("\\n".join(current_lines).strip(), current_heading))

    return [(text, span) for text, span in chunks if text]


def _vector_literal(values: list[float]) -> str:
    """Format a pgvector literal without relying on an extra adapter package."""
    return "[" + ",".join(format(float(v), ".9g") for v in values) + "]"


def _load_existing_source(conn, organization_id: str, content_hash: str):
    return conn.execute(
        """
        SELECT id, content_hash
        FROM sources
        WHERE organization_id = %s AND content_hash = %s
        LIMIT 1
        """,
        (organization_id, content_hash),
    ).fetchone()


def _seed_state(conn, source_id: str) -> tuple[int, int]:
    knowledge = conn.execute(
        "SELECT COUNT(*) AS count FROM knowledge_items WHERE source_id = %s",
        (source_id,),
    ).fetchone()
    chunks = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM source_chunks sc
        JOIN source_documents sd ON sd.id = sc.source_document_id
        WHERE sd.source_id = %s
        """,
        (source_id,),
    ).fetchone()
    return int(knowledge["count"] if knowledge else 0), int(chunks["count"] if chunks else 0)


def _cleanup_seed_artifacts(conn, source_id: str) -> None:
    conn.execute(
        """
        DELETE FROM embeddings
        WHERE metadata ->> 'source_id' = %s
        """,
        (source_id,),
    )
    conn.execute(
        "DELETE FROM knowledge_items WHERE source_id = %s",
        (source_id,),
    )
    conn.execute(
        "DELETE FROM source_documents WHERE source_id = %s",
        (source_id,),
    )


def _get_organization_id(conn) -> str:
    row = conn.execute(
        "SELECT id FROM organizations WHERE slug = %s LIMIT 1", (ORGANIZATION_SLUG,)
    ).fetchone()
    if not row:
        raise RuntimeError("Organization 'us-bcsd' is missing; run migrations first")
    return str(row["id"])


def _extract(content: str) -> ExtractionSchema:
    provider = GeminiProvider()
    extractor = KnowledgeExtractor(provider=provider)
    return extractor.extract(content)


def _run_seed() -> None:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if not SEED_PATH.exists():
        raise FileNotFoundError(f"Seed source not found: {SEED_PATH}")

    content = SEED_PATH.read_text(encoding="utf-8").strip()
    content_hash = sha256_text(content)
    normalized = normalize_text(
        content,
        source_type="seed",
        title="US BCSD Seed Knowledge",
        source_external_id=content_hash,
        access_scope="ORGANIZATION",
    )
    chunks = _chunk_markdown(normalized.content)

    print(f"[SEED] source={SEED_PATH.name} sha256={content_hash} bytes={len(content.encode('utf-8'))}")

    with connection() as conn:
        organization_id = _get_organization_id(conn)
        existing = _load_existing_source(conn, organization_id, content_hash)
        if existing:
            existing_id = str(existing["id"])
            knowledge_count, chunk_count = _seed_state(conn, existing_id)
            if knowledge_count > 0 and chunk_count == len(chunks):
                print(f"[SEED] already ingested source_id={existing_id}; nothing to do")
                return
            if knowledge_count > 0 or chunk_count > 0:
                print(
                    f"[SEED] existing source is incomplete (chunks={chunk_count}, "
                    f"knowledge_items={knowledge_count}); rebuilding derived memory"
                )
                _cleanup_seed_artifacts(conn, existing_id)

    print("[EXTRACT] extracting structured knowledge with Gemini")
    extraction = _extract(normalized.content)
    print(f"[EXTRACT] knowledge_objects={len(extraction.knowledge_objects)}")

    embedding_service = EmbeddingService()
    chunk_embeddings: list[list[float]] = []
    for index, (chunk_text, _) in enumerate(chunks):
        print(f"[EMBED] chunk {index + 1}/{len(chunks)}")
        chunk_embeddings.append(embedding_service.embed(chunk_text))

    knowledge_embeddings: list[list[float]] = []
    for index, obj in enumerate(extraction.knowledge_objects):
        print(f"[EMBED] knowledge {index + 1}/{len(extraction.knowledge_objects)}")
        knowledge_embeddings.append(embedding_service.embed(obj.statement))

    source_id = str(uuid4())
    document_id = str(uuid4())
    now = datetime.now(timezone.utc)

    with connection(organization_id=organization_id) as conn:
        existing = _load_existing_source(conn, organization_id, content_hash)
        if existing:
            source_id = str(existing["id"])
        else:
            conn.execute(
                """
                INSERT INTO sources (
                    id, source_type, external_id, title, captured_at, content_hash,
                    access_scope, organization_id, metadata
                ) VALUES (%s, 'seed', %s, %s, %s, %s, 'ORGANIZATION', %s, %s)
                """,
                (
                    source_id,
                    content_hash,
                    "US BCSD Seed Knowledge",
                    now,
                    content_hash,
                    organization_id,
                    json.dumps({"seed_path": str(SEED_PATH.relative_to(REPO_ROOT)), "parser_version": PARSER_VERSION}),
                ),
            )

        conn.execute(
            """
            INSERT INTO source_documents (
                id, source_id, document_type, raw_text, structured_content,
                parser_version, language, extraction_status
            ) VALUES (%s, %s, 'markdown', %s, %s, %s, 'en', 'completed')
            """,
            (document_id, source_id, normalized.content, extraction.model_dump_json(), PARSER_VERSION),
        )

        for index, ((chunk_text, span), embedding) in enumerate(zip(chunks, chunk_embeddings)):
            chunk_id = str(uuid4())
            vector = _vector_literal(embedding)
            conn.execute(
                """
                INSERT INTO source_chunks (
                    id, source_document_id, chunk_index, chunk_text, source_span,
                    locator, embedding, embedding_model, embedding_version, embedding_dimensions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s)
                """,
                (
                    chunk_id,
                    document_id,
                    index,
                    chunk_text,
                    span,
                    json.dumps({"chunk_index": index}),
                    vector,
                    settings.gemini_embedding_model,
                    EMBEDDING_VERSION,
                    len(embedding),
                ),
            )
            conn.execute(
                """
                INSERT INTO embeddings (
                    object_type, object_id, chunk_text, embedding, embedding_model,
                    embedding_version, embedding_dimensions, metadata, organization_id
                ) VALUES ('source_chunk', %s, %s, %s::vector, %s, %s, %s, %s, %s)
                """,
                (
                    chunk_id,
                    chunk_text,
                    vector,
                    settings.gemini_embedding_model,
                    EMBEDDING_VERSION,
                    len(embedding),
                    json.dumps({"source_id": source_id, "source_document_id": document_id}),
                    organization_id,
                ),
            )

        for index, (obj, embedding) in enumerate(zip(extraction.knowledge_objects, knowledge_embeddings)):
            knowledge_id = str(uuid4())
            project_id = None
            statement = obj.statement.strip()
            truth_class = obj.truth_class.strip() or "candidate"
            conn.execute(
                """
                INSERT INTO knowledge_items (
                    id, knowledge_type, statement, project_id, status, truth_class,
                    confidence, source_id, source_span, access_scope, access_scope_ref,
                    created_by_type, organization_id
                ) VALUES (%s, %s, %s, %s, 'candidate', %s, %s, %s, %s, 'ORGANIZATION', NULL, 'system', %s)
                """,
                (
                    knowledge_id,
                    obj.type.strip() or "context",
                    statement,
                    project_id,
                    truth_class,
                    obj.confidence,
                    source_id,
                    obj.source_span,
                    organization_id,
                ),
            )
            conn.execute(
                """
                INSERT INTO knowledge_versions (
                    knowledge_item_id, previous_value, new_value, change_type,
                    source_id, changed_by_type
                ) VALUES (%s, NULL, %s, 'created', %s, 'system')
                """,
                (
                    knowledge_id,
                    json.dumps(obj.model_dump()),
                    source_id,
                ),
            )
            vector = _vector_literal(embedding)
            conn.execute(
                """
                INSERT INTO embeddings (
                    object_type, object_id, chunk_text, embedding, embedding_model,
                    embedding_version, embedding_dimensions, metadata, organization_id
                ) VALUES ('knowledge_item', %s, %s, %s::vector, %s, %s, %s, %s, %s)
                """,
                (
                    knowledge_id,
                    statement,
                    vector,
                    settings.gemini_embedding_model,
                    EMBEDDING_VERSION,
                    len(embedding),
                    json.dumps({"source_id": source_id, "knowledge_type": obj.type, "extraction_index": index}),
                    organization_id,
                ),
            )

        print(
            f"[COMPLETE] source_id={source_id} document_id={document_id} "
            f"chunks={len(chunks)} knowledge_items={len(extraction.knowledge_objects)} "
            f"embedding_dimensions={len(chunk_embeddings[0]) if chunk_embeddings else settings.gemini_embedding_dimensions}"
        )


def main() -> None:
    try:
        _run_seed()
    finally:
        close_pool()


if __name__ == "__main__":
    main()
