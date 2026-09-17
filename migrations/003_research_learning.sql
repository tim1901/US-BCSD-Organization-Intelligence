CREATE TABLE IF NOT EXISTS research_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), request_id TEXT UNIQUE, project_id UUID REFERENCES projects(id),
  question TEXT NOT NULL, research_depth TEXT NOT NULL DEFAULT 'standard', status TEXT NOT NULL DEFAULT 'queued',
  budget JSONB NOT NULL DEFAULT '{}'::jsonb, started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, error TEXT,
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS research_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), research_job_id UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
  source_id UUID REFERENCES sources(id), role TEXT, quality_score NUMERIC(5,2), retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS research_findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), research_job_id UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
  claim TEXT NOT NULL, finding_type TEXT NOT NULL DEFAULT 'verified_fact', evidence_text TEXT, confidence NUMERIC(5,4),
  source_id UUID REFERENCES sources(id), access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION', access_scope_ref TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS research_steps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), research_job_id UUID NOT NULL REFERENCES research_jobs(id) ON DELETE CASCADE,
  step_number INTEGER NOT NULL, action_type TEXT NOT NULL, query_or_action TEXT, source_id UUID REFERENCES sources(id),
  result_status TEXT, selection_status TEXT, concise_rationale TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS research_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), canonical_title TEXT NOT NULL, description TEXT, event_date TIMESTAMPTZ,
  first_seen_at TIMESTAMPTZ, last_seen_at TIMESTAMPTZ, confidence NUMERIC(5,4), organization_id UUID NOT NULL REFERENCES organizations(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS assistant_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id UUID REFERENCES conversations(id), request_id TEXT, user_identity_id UUID REFERENCES identities(id),
  intent TEXT, project_id UUID REFERENCES projects(id), status TEXT NOT NULL DEFAULT 'running', model_name TEXT, thinking_level TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), completed_at TIMESTAMPTZ, input_token_count INTEGER, output_token_count INTEGER,
  estimated_cost NUMERIC(12,6), final_response TEXT, organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS tool_calls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), assistant_run_id UUID NOT NULL REFERENCES assistant_runs(id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL, input_summary JSONB, output_summary JSONB, status TEXT NOT NULL, started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, error_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS evidence_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), claim_object_type TEXT NOT NULL, claim_object_id UUID NOT NULL,
  source_id UUID REFERENCES sources(id), source_span TEXT, locator JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence_role TEXT NOT NULL DEFAULT 'supports', confidence NUMERIC(5,4), organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS citations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), assistant_run_id UUID NOT NULL REFERENCES assistant_runs(id) ON DELETE CASCADE,
  source_id UUID REFERENCES sources(id), knowledge_item_id UUID REFERENCES knowledge_items(id), research_finding_id UUID REFERENCES research_findings(id),
  claim_text TEXT, locator JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id TEXT, conversation_id UUID REFERENCES conversations(id), message_id UUID REFERENCES messages(id),
  feedback_type TEXT NOT NULL, feedback_text TEXT, related_object_type TEXT, related_object_id UUID, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS learning_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), learning_type TEXT NOT NULL, trigger_source_type TEXT, trigger_source_id TEXT,
  affected_object_type TEXT, affected_object_id UUID, previous_state JSONB, new_state JSONB, confidence NUMERIC(5,4),
  validation_status TEXT NOT NULL DEFAULT 'candidate', organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), job_type TEXT NOT NULL, payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  priority INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'queued', available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 5, locked_at TIMESTAMPTZ, locked_by TEXT,
  started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, last_error TEXT, idempotency_key TEXT UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), organization_id UUID REFERENCES organizations(id), actor_type TEXT NOT NULL,
  actor_id TEXT, action TEXT NOT NULL, target_type TEXT, target_id TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS slack_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), event_id TEXT UNIQUE NOT NULL, workspace_id TEXT NOT NULL, event_type TEXT NOT NULL,
  payload_hash TEXT NOT NULL, received_at TIMESTAMPTZ NOT NULL, retry_number INTEGER NOT NULL DEFAULT 0,
  processing_status TEXT NOT NULL DEFAULT 'received', processed_at TIMESTAMPTZ, error_code TEXT, raw_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
