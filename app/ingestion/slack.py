from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.ai.embeddings import EmbeddingService
from app.core.config import settings
from app.ingestion.extractors import KnowledgeExtractor
from app.integrations.slack import SlackClient
from app.storage.repositories.jobs import JobRepository
from app.storage.supabase import connection

ORGANIZATION_SLUG = "us-bcsd"
PARSER_VERSION = "slack-thread-v1"
EMBEDDING_VERSION = "gemini-embedding-v1"


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(format(float(value), ".9g") for value in values) + "]"


def _ts_datetime(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def _message_text(message: dict[str, Any]) -> str:
    text = str(message.get("text") or "").strip()
    if text:
        return text
    files = message.get("files") or []
    if files:
        return "[Slack message with file attachment]"
    return ""


def _thread_key(workspace_id: str, channel_id: str, thread_ts: str) -> str:
    return f"slack:thread:{workspace_id}:{channel_id}:{thread_ts}"


class SlackIngestionService:
    def __init__(
        self,
        *,
        slack: SlackClient | None = None,
        extractor: KnowledgeExtractor | None = None,
        embeddings: EmbeddingService | None = None,
    ):
        self.slack = slack or SlackClient()
        self.extractor = extractor or KnowledgeExtractor()
        self.embeddings = embeddings or EmbeddingService()

    @staticmethod
    def organization_id() -> str:
        with connection() as conn:
            row = conn.execute(
                "SELECT id FROM organizations WHERE slug = %s LIMIT 1",
                (ORGANIZATION_SLUG,),
            ).fetchone()
        if not row:
            raise RuntimeError("Organization 'us-bcsd' is missing; run migrations first")
        return str(row["id"])

    def sync_workspace(self, *, all_channels: bool = True, channel_ids: list[str] | None = None) -> int:
        org_id = self.organization_id()
        workspace_id = settings.slack_workspace_id
        if not workspace_id:
            raise RuntimeError("SLACK_WORKSPACE_ID is not configured")

        users = self.slack.users()
        self._upsert_users(org_id, workspace_id, users)

        channels = self.slack.channels()
        selected = {
            item["id"]
            for item in channels
            if all_channels or (channel_ids and item["id"] in set(channel_ids))
        }

        self._upsert_channels(org_id, workspace_id, channels)

        jobs = JobRepository()
        queued = 0
        for channel in channels:
            channel_id = channel["id"]
            if channel_id not in selected:
                continue
            if channel.get("is_archived"):
                continue
            jobs.enqueue(
                "backfill_slack_channel",
                {
                    "organization_id": org_id,
                    "workspace_id": workspace_id,
                    "channel_id": channel_id,
                    "channel_name": channel.get("name"),
                },
                idempotency_key=f"slack:backfill:{workspace_id}:{channel_id}:{datetime.now(timezone.utc).date().isoformat()}",
                priority=10,
                max_attempts=settings.job_max_attempts,
            )
            queued += 1
        return queued

    def backfill_channel(self, job: dict[str, Any]) -> int:
        workspace_id = str(job["workspace_id"])
        channel_id = str(job["channel_id"])
        messages = self.slack.history(channel_id)
        jobs = JobRepository()
        roots: set[str] = set()
        for message in messages:
            message_type = message.get("type")
            if message_type != "message":
                continue
            text = _message_text(message)
            thread_ts = str(message.get("thread_ts") or message.get("ts") or "")
            if not thread_ts or not text:
                continue
            root_ts = str(message.get("thread_ts") or message.get("ts"))
            roots.add(root_ts)

        for root_ts in roots:
            jobs.enqueue(
                "ingest_slack_thread",
                {
                    "organization_id": job["organization_id"],
                    "workspace_id": workspace_id,
                    "channel_id": channel_id,
                    "thread_ts": root_ts,
                },
                idempotency_key=_thread_key(workspace_id, channel_id, root_ts),
                priority=5,
                max_attempts=settings.job_max_attempts,
            )

        with connection(job["organization_id"]) as conn:
            conn.execute(
                """
                UPDATE slack_channels
                SET last_backfilled_at = NOW(), updated_at = NOW()
                WHERE workspace_id = %s AND channel_id = %s
                """,
                (workspace_id, channel_id),
            )
        return len(roots)

    def ingest_event(self, job: dict[str, Any]) -> None:
        event_id = str(job["slack_event_id"])
        with connection() as conn:
            row = conn.execute(
                "SELECT raw_payload FROM slack_events WHERE event_id = %s LIMIT 1",
                (event_id,),
            ).fetchone()
        if not row:
            raise RuntimeError(f"Slack event {event_id} not found")

        payload = row["raw_payload"]
        event = payload.get("event", {})
        message = event.get("message") or event
        channel_id = event.get("channel") or message.get("channel")
        event_type = event.get("type")
        channel_type = event.get("channel_type") or message.get("channel_type")

        if event_type != "message" or channel_type not in {"channel", "group"} or not channel_id:
            self._mark_event(event_id, "ignored", None)
            return

        thread_ts = str(
            event.get("thread_ts")
            or event.get("ts")
            or message.get("thread_ts")
            or message.get("ts")
            or ""
        )
        if not thread_ts:
            self._mark_event(event_id, "ignored", "missing_thread_ts")
            return

        self._mark_event(event_id, "processing", None)
        try:
            self.ingest_thread(
                organization_id=self.organization_id(),
                workspace_id=str(payload.get("team_id") or settings.slack_workspace_id),
                channel_id=str(channel_id),
                thread_ts=thread_ts,
            )
            self._mark_event(event_id, "processed", None)
        except Exception as exc:
            self._mark_event(event_id, "error", type(exc).__name__)
            raise

    def ingest_thread(
        self,
        *,
        organization_id: str,
        workspace_id: str,
        channel_id: str,
        thread_ts: str,
    ) -> str:
        messages = self.slack.replies(channel_id, thread_ts)
        messages = [m for m in messages if m.get("type") == "message"]
        if not messages:
            return ""

        messages.sort(key=lambda item: float(item.get("ts", "0")))
        channel_name = self._channel_name(workspace_id, channel_id)
        participants = self._ensure_message_identities(organization_id, workspace_id, messages)
        content_parts: list[str] = []
        for message in messages:
            text = _message_text(message)
            if not text:
                continue
            user_id = str(message.get("user") or "unknown")
            person_name = participants.get(user_id, user_id)
            content_parts.append(f"{person_name}: {text}")

        combined = "\n".join(content_parts).strip()
        if not combined or len(combined) < settings.slack_min_text_chars:
            self._persist_messages_only(
                organization_id, workspace_id, channel_id, thread_ts, channel_name, messages
            )
            return ""

        now = datetime.now(timezone.utc)
        source_id = self._upsert_source(
            organization_id=organization_id,
            workspace_id=workspace_id,
            channel_id=channel_id,
            channel_name=channel_name,
            thread_ts=thread_ts,
            combined_text=combined,
            root_message=messages[0],
            captured_at=now,
        )

        self._replace_memory_for_source(
            organization_id=organization_id,
            source_id=source_id,
            channel_id=channel_id,
            channel_name=channel_name,
            thread_ts=thread_ts,
            messages=messages,
            combined_text=combined,
        )

        self._persist_conversation_messages(
            organization_id,
            workspace_id,
            channel_id,
            thread_ts,
            channel_name,
            source_id,
            messages,
        )
        return source_id

    def _channel_name(self, workspace_id: str, channel_id: str) -> str:
        with connection() as conn:
            row = conn.execute(
                "SELECT channel_name FROM slack_channels WHERE workspace_id = %s AND channel_id = %s LIMIT 1",
                (workspace_id, channel_id),
            ).fetchone()
        return str(row["channel_name"] if row and row["channel_name"] else channel_id)

    def _upsert_users(self, organization_id: str, workspace_id: str, users: list[dict[str, Any]]) -> None:
        with connection(organization_id) as conn:
            for user in users:
                external_id = str(user.get("id") or "")
                if not external_id:
                    continue
                name = str(user.get("real_name") or user.get("name") or external_id).strip()
                person = conn.execute(
                    """
                    SELECT id FROM people
                    WHERE organization_id = %s
                      AND normalized_name = LOWER(%s)
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (organization_id, name),
                ).fetchone()
                if person:
                    person_id = str(person["id"])
                    conn.execute(
                        "UPDATE people SET title = COALESCE(%s, title), metadata = metadata || %s::jsonb, updated_at = NOW() WHERE id = %s",
                        (
                            (user.get("profile") or {}).get("title"),
                            json.dumps({"slack_user_id": external_id}),
                            person_id,
                        ),
                    )
                else:
                    person_id = str(uuid4())
                    conn.execute(
                        """
                        INSERT INTO people(id, name, normalized_name, organization_id, title, metadata)
                        VALUES(%s, %s, %s, %s, %s, %s::jsonb)
                        """,
                        (
                            person_id,
                            name,
                            name.lower(),
                            organization_id,
                            (user.get("profile") or {}).get("title"),
                            json.dumps({"slack_user_id": external_id}),
                        ),
                    )
                conn.execute(
                    """
                    INSERT INTO identities(id, person_id, provider, external_user_id, workspace_id, metadata)
                    VALUES(%s, %s, 'slack', %s, %s, %s::jsonb)
                    ON CONFLICT(provider, external_user_id, workspace_id)
                    DO UPDATE SET person_id = EXCLUDED.person_id, metadata = EXCLUDED.metadata, updated_at = NOW()
                    """,
                    (
                        str(uuid4()),
                        person_id,
                        external_id,
                        workspace_id,
                        json.dumps({"deleted": bool(user.get("deleted")), "is_bot": bool(user.get("is_bot"))}),
                    ),
                )

    def _upsert_channels(self, organization_id: str, workspace_id: str, channels: list[dict[str, Any]]) -> None:
        with connection(organization_id) as conn:
            for channel in channels:
                conn.execute(
                    """
                    INSERT INTO slack_channels(
                        workspace_id, channel_id, channel_name, visibility, private,
                        enabled_for_ingestion, enabled_for_interaction, created_at, updated_at
                    )
                    VALUES(%s, %s, %s, %s, %s, TRUE, TRUE, NOW(), NOW())
                    ON CONFLICT(workspace_id, channel_id)
                    DO UPDATE SET
                        channel_name = EXCLUDED.channel_name,
                        visibility = EXCLUDED.visibility,
                        private = EXCLUDED.private,
                        updated_at = NOW()
                    """,
                    (
                        workspace_id,
                        str(channel["id"]),
                        channel.get("name"),
                        "private" if channel.get("is_private") else "public",
                        bool(channel.get("is_private")),
                    ),
                )

    def _ensure_message_identities(
        self,
        organization_id: str,
        workspace_id: str,
        messages: list[dict[str, Any]],
    ) -> dict[str, str]:
        user_ids = {str(m.get("user")) for m in messages if m.get("user")}
        if not user_ids:
            return {}
        result: dict[str, str] = {}
        with connection(organization_id) as conn:
            rows = conn.execute(
                """
                SELECT i.external_user_id, p.name
                FROM identities i
                JOIN people p ON p.id = i.person_id
                WHERE i.provider = 'slack'
                  AND i.workspace_id = %s
                  AND i.external_user_id = ANY(%s)
                """,
                (workspace_id, list(user_ids)),
            ).fetchall()
            for row in rows:
                result[str(row["external_user_id"])] = str(row["name"])
        return result

    def _upsert_source(
        self,
        *,
        organization_id: str,
        workspace_id: str,
        channel_id: str,
        channel_name: str,
        thread_ts: str,
        combined_text: str,
        root_message: dict[str, Any],
        captured_at: datetime,
    ) -> str:
        external_id = f"slack:{workspace_id}:{channel_id}:{thread_ts}"
        content_hash = hashlib.sha256(
            f"{external_id}\n{combined_text}".encode("utf-8")
        ).hexdigest()
        with connection(organization_id) as conn:
            row = conn.execute(
                """
                SELECT id FROM sources
                WHERE organization_id = %s AND external_id = %s
                LIMIT 1
                """,
                (organization_id, external_id),
            ).fetchone()
            source_id = str(row["id"]) if row else str(uuid4())
            if row:
                conn.execute(
                    """
                    UPDATE sources
                    SET title = %s, author = %s, published_at = %s, captured_at = %s,
                        content_hash = %s, metadata = %s::jsonb
                    WHERE id = %s
                    """,
                    (
                        f"Slack #{channel_name} thread {thread_ts}",
                        str(root_message.get("user") or ""),
                        _ts_datetime(root_message.get("ts")),
                        captured_at,
                        content_hash,
                        json.dumps({"workspace_id": workspace_id, "channel_id": channel_id, "thread_ts": thread_ts}),
                        source_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO sources(
                        id, source_type, external_id, title, author, published_at, captured_at,
                        content_hash, access_scope, organization_id, metadata
                    )
                    VALUES(%s, 'slack_thread', %s, %s, %s, %s, %s, %s, 'ORGANIZATION', %s, %s::jsonb)
                    """,
                    (
                        source_id,
                        external_id,
                        f"Slack #{channel_name} thread {thread_ts}",
                        str(root_message.get("user") or ""),
                        _ts_datetime(root_message.get("ts")),
                        captured_at,
                        content_hash,
                        organization_id,
                        json.dumps({"workspace_id": workspace_id, "channel_id": channel_id, "thread_ts": thread_ts}),
                    ),
                )
        return source_id

    def _replace_memory_for_source(
        self,
        *,
        organization_id: str,
        source_id: str,
        channel_id: str,
        channel_name: str,
        thread_ts: str,
        messages: list[dict[str, Any]],
        combined_text: str,
    ) -> None:
        extraction = self.extractor.extract(combined_text)
        embedding = self.embeddings.embed(combined_text)
        knowledge_embeddings = [
            self.embeddings.embed(obj.statement.strip())
            for obj in extraction.knowledge_objects
        ]
        document_id = str(uuid4())
        chunk_id = str(uuid4())
        vector = _vector_literal(embedding)
        source_span = f"Slack #{channel_name} thread {thread_ts}"

        with connection(organization_id) as conn:
            conn.execute(
                "DELETE FROM embeddings WHERE metadata ->> 'source_id' = %s",
                (source_id,),
            )
            conn.execute("DELETE FROM knowledge_items WHERE source_id = %s", (source_id,))
            conn.execute("DELETE FROM source_documents WHERE source_id = %s", (source_id,))

            conn.execute(
                """
                INSERT INTO source_documents(
                    id, source_id, document_type, raw_text, structured_content,
                    parser_version, language, extraction_status
                )
                VALUES(%s, %s, 'slack_thread', %s, %s::jsonb, %s, 'en', 'completed')
                """,
                (
                    document_id,
                    source_id,
                    combined_text,
                    json.dumps(
                        {
                            "channel_id": channel_id,
                            "channel_name": channel_name,
                            "thread_ts": thread_ts,
                            "message_count": len(messages),
                        }
                    ),
                    PARSER_VERSION,
                ),
            )
            conn.execute(
                """
                INSERT INTO source_chunks(
                    id, source_document_id, chunk_index, chunk_text, source_span,
                    locator, embedding, embedding_model, embedding_version, embedding_dimensions
                )
                VALUES(%s, %s, 0, %s, %s, %s::jsonb, %s::vector, %s, %s, %s)
                """,
                (
                    chunk_id,
                    document_id,
                    combined_text,
                    source_span,
                    json.dumps(
                        {
                            "channel_id": channel_id,
                            "thread_ts": thread_ts,
                            "message_ts": [str(m.get("ts")) for m in messages if m.get("ts")],
                        }
                    ),
                    vector,
                    settings.gemini_embedding_model,
                    EMBEDDING_VERSION,
                    len(embedding),
                ),
            )
            conn.execute(
                """
                INSERT INTO embeddings(
                    object_type, object_id, chunk_text, embedding, embedding_model,
                    embedding_version, embedding_dimensions, metadata, organization_id
                )
                VALUES('source_chunk', %s, %s, %s::vector, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    chunk_id,
                    combined_text,
                    vector,
                    settings.gemini_embedding_model,
                    EMBEDDING_VERSION,
                    len(embedding),
                    json.dumps(
                        {
                            "source_id": source_id,
                            "channel_id": channel_id,
                            "thread_ts": thread_ts,
                            "source_span": source_span,
                        }
                    ),
                    organization_id,
                ),
            )

            for obj, knowledge_embedding in zip(extraction.knowledge_objects, knowledge_embeddings):
                knowledge_id = str(uuid4())
                statement = obj.statement.strip()
                conn.execute(
                    """
                    INSERT INTO knowledge_items(
                        id, knowledge_type, statement, status, truth_class, confidence,
                        source_id, source_span, access_scope, created_by_type, organization_id
                    )
                    VALUES(%s, %s, %s, 'candidate', %s, %s, %s, %s, 'ORGANIZATION', 'system', %s)
                    """,
                    (
                        knowledge_id,
                        obj.type.strip() or "context",
                        statement,
                        obj.truth_class.strip() or "candidate",
                        obj.confidence,
                        source_id,
                        obj.source_span or source_span,
                        organization_id,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO knowledge_versions(
                        knowledge_item_id, previous_value, new_value, change_type,
                        source_id, changed_by_type
                    )
                    VALUES(%s, NULL, %s::jsonb, 'created', %s, 'system')
                    """,
                    (
                        knowledge_id,
                        obj.model_dump_json(),
                        source_id,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO embeddings(
                        object_type, object_id, chunk_text, embedding, embedding_model,
                        embedding_version, embedding_dimensions, metadata, organization_id
                    )
                    VALUES('knowledge_item', %s, %s, %s::vector, %s, %s, %s, %s::jsonb, %s)
                    """,
                    (
                        knowledge_id,
                        statement,
                        _vector_literal(knowledge_embedding),
                        settings.gemini_embedding_model,
                        EMBEDDING_VERSION,
                        len(knowledge_embedding),
                        json.dumps(
                            {
                                "source_id": source_id,
                                "source_span": obj.source_span or source_span,
                                "knowledge_type": obj.type,
                            }
                        ),
                        organization_id,
                    ),
                )

    def _persist_conversation_messages(
        self,
        organization_id: str,
        workspace_id: str,
        channel_id: str,
        thread_ts: str,
        channel_name: str,
        source_id: str | None,
        messages: list[dict[str, Any]],
    ) -> None:
        with connection(organization_id) as conn:
            row = conn.execute(
                """
                SELECT id FROM conversations
                WHERE channel_id = %s AND thread_external_id = %s
                LIMIT 1
                """,
                (channel_id, thread_ts),
            ).fetchone()
            conversation_id = str(row["id"]) if row else str(uuid4())
            started = _ts_datetime(messages[0].get("ts"))
            ended = _ts_datetime(messages[-1].get("ts"))
            if row:
                conn.execute(
                    """
                    UPDATE conversations
                    SET source_id = %s, started_at = %s, ended_at = %s, metadata = %s::jsonb
                    WHERE id = %s
                    """,
                    (
                        source_id,
                        started,
                        ended,
                        json.dumps({"workspace_id": workspace_id, "channel_name": channel_name}),
                        conversation_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO conversations(
                        id, source_id, channel_id, thread_external_id, conversation_type,
                        started_at, ended_at, access_scope, organization_id, metadata
                    )
                    VALUES(%s, %s, %s, %s, 'slack_thread', %s, %s, 'ORGANIZATION', %s, %s::jsonb)
                    """,
                    (
                        conversation_id,
                        source_id,
                        channel_id,
                        thread_ts,
                        started,
                        ended,
                        organization_id,
                        json.dumps({"workspace_id": workspace_id, "channel_name": channel_name}),
                    ),
                )

            for message in messages:
                external_message_id = str(message.get("ts") or "")
                if not external_message_id:
                    continue
                author_person_id = self._person_id_for_slack_user(
                    conn,
                    workspace_id,
                    str(message.get("user") or ""),
                )
                reply_to_id = None
                parent_ts = message.get("thread_ts")
                if parent_ts and str(parent_ts) != external_message_id:
                    parent = conn.execute(
                        """
                        SELECT id FROM messages
                        WHERE conversation_id = %s AND external_message_id = %s
                        LIMIT 1
                        """,
                        (conversation_id, str(parent_ts)),
                    ).fetchone()
                    reply_to_id = str(parent["id"]) if parent else None

                conn.execute(
                    """
                    INSERT INTO messages(
                        id, conversation_id, external_message_id, author_person_id, content,
                        message_ts, reply_to_message_id, raw_payload, access_scope, created_at
                    )
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s::jsonb, 'ORGANIZATION', NOW())
                    ON CONFLICT(conversation_id, external_message_id)
                    DO UPDATE SET
                        author_person_id = EXCLUDED.author_person_id,
                        content = EXCLUDED.content,
                        message_ts = EXCLUDED.message_ts,
                        raw_payload = EXCLUDED.raw_payload
                    """,
                    (
                        str(uuid4()),
                        conversation_id,
                        external_message_id,
                        author_person_id,
                        _message_text(message),
                        _ts_datetime(message.get("ts")),
                        reply_to_id,
                        json.dumps(message),
                    ),
                )

    @staticmethod
    def _persist_messages_only(
        organization_id: str,
        workspace_id: str,
        channel_id: str,
        thread_ts: str,
        channel_name: str,
        messages: list[dict[str, Any]],
    ) -> None:
        # Keep message history even when a thread is too short to justify an AI extraction call.
        service = SlackIngestionService.__new__(SlackIngestionService)
        service._persist_conversation_messages(
            organization_id,
            workspace_id,
            channel_id,
            thread_ts,
            channel_name,
            None,
            messages,
        )

    @staticmethod
    def _person_id_for_slack_user(conn, workspace_id: str, external_user_id: str) -> str | None:
        if not external_user_id:
            return None
        row = conn.execute(
            """
            SELECT person_id FROM identities
            WHERE provider = 'slack' AND workspace_id = %s AND external_user_id = %s
            LIMIT 1
            """,
            (workspace_id, external_user_id),
        ).fetchone()
        return str(row["person_id"]) if row and row["person_id"] else None

    def _mark_event(self, event_id: str, status: str, error_code: str | None) -> None:
        with connection() as conn:
            conn.execute(
                """
                UPDATE slack_events
                SET processing_status = %s, processed_at = CASE WHEN %s = 'processed' THEN NOW() ELSE processed_at END,
                    error_code = %s
                WHERE event_id = %s
                """,
                (status, status, error_code, event_id),
            )
