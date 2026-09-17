# US BCSD Organizational Intelligence

Production-oriented modular Python monolith implementing the locked US BCSD Organizational Intelligence architecture.

## Architecture boundaries

The repository contains seven logical systems inside one application:

1. Input / Ingestion
2. Organizational Memory
3. AI Brain
4. Intelligence Engine
5. Slack Delivery / Interface
6. Learning / Feedback
7. Orchestration / Control

Supporting layers are separated into AI provider, storage, models, core security/configuration, and connectors.

## Runtime

- FastAPI Web Service
- Render Background Worker
- Render Cron Job
- Supabase PostgreSQL + pgvector + private Storage
- Paid Gemini via Gemini Interactions API
- Slack Events API + Web API
- PostgreSQL-backed job queue

## Important boundaries

- PostgreSQL is canonical structured organizational state.
- pgvector is retrieval infrastructure, never the canonical source of truth.
- Gemini organizational calls default to `store=false`.
- Google Search grounding is only for sanitized public research queries.
- External web content and uploaded files are untrusted.
- Private Slack data retains its access scope until explicit audited promotion.
- Email/Asana/Calendar execution is outside the initial product boundary.
- No n8n, Redis, Kafka, or multi-agent framework dependency.

## Local setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run migrations in order against Supabase/PostgreSQL, then:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
python -m app.orchestration.worker
python -m app.orchestration.scheduler
```

## Render

`render.yaml` defines the Web Service, Background Worker, and Cron Job. Secrets are not committed; enter them in Render.

## Architecture alignment

`ARCHITECTURE_ALIGNMENT.md` maps the repository directly to the locked technical architecture.
