# Architecture Alignment

This repository is intentionally structured from the locked technical architecture rather than from a simplified starter template.

| Locked architecture boundary | Implementation location |
| --- | --- |
| Input / Ingestion | `app/ingestion/` |
| Connectors | `app/connectors/` |
| Organizational Memory | `app/memory/` + `app/storage/repositories/` |
| AI Brain | `app/brain/` |
| Intelligence Engine | `app/intelligence/` |
| Learning / Feedback | `app/learning/` |
| Slack Delivery | `app/delivery/` + `app/api/routes_slack.py` |
| Orchestration / Control | `app/orchestration/` |
| AI provider abstraction | `app/ai/provider.py`, `app/ai/gemini.py` |
| Storage | `app/storage/` |
| Domain models | `app/models/` |
| Provenance / evidence graph | `app/memory/provenance.py`, `evidence_links`, `citations` migrations |
| Temporal / supersession | `app/memory/temporal.py`, `knowledge_versions`, supersession fields |
| Conflict detection | `app/memory/conflicts.py` |
| Hybrid retrieval | `app/memory/hybrid_search.py` |
| Resumable Slack backfill | `app/connectors/slack.py`, `app/orchestration/jobs.py` |
| Slack receipt/idempotency | `slack_events`, `app/api/routes_slack.py` |
| Bounded research | `app/intelligence/` |
| Cost control | `app/intelligence/budget.py`, `app/orchestration/` |
| Learning ledger | `app/learning/`, `learning_events` |
| Benchmark suite | `tests/benchmarks/`, `app/learning/benchmark.py` |
| Access scope / restricted inheritance | `app/core/security.py`, memory retrieval filters, migration policies |
| Private Storage | `app/storage/object_storage.py` |
| Seed knowledge | `knowledge/seed/`, `scripts/seed_knowledge.py` |

## API surface alignment

- `GET /health` → `app/api/routes_health.py`
- `GET /health/dependencies` → `app/api/routes_health.py`
- `POST /api/ingest/text|file|url` → `app/api/routes_ingestion.py`
- `POST /api/slack/events|command` → `app/api/routes_slack.py`
- `POST /api/research/start`, `GET /api/research/{job_id}` → `app/api/routes_research.py`
- `POST /api/brain/ask` → `app/api/routes_brain.py`
- `POST /api/feedback` → `app/api/routes_feedback.py`
- `GET /api/projects/{project_id}` and `/context` → `app/api/routes_projects.py`
- `POST /api/admin/reindex|backfill`, `GET /api/admin/jobs/{job_id}` → `app/api/routes_admin.py`
