CREATE INDEX IF NOT EXISTS ix_knowledge_project ON knowledge_items(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_knowledge_scope ON knowledge_items(access_scope, access_scope_ref);
CREATE INDEX IF NOT EXISTS ix_messages_conversation ON messages(conversation_id, message_ts);
CREATE INDEX IF NOT EXISTS ix_jobs_queue ON jobs(status, available_at, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS ix_research_jobs_status ON research_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS ix_learning_events ON learning_events(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_evidence_claim ON evidence_links(claim_object_type, claim_object_id);
CREATE INDEX IF NOT EXISTS ix_slack_events_status ON slack_events(processing_status, received_at);

CREATE OR REPLACE FUNCTION current_organization_id() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_organization_id', true), '')::uuid;
$$;

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS org_projects ON projects;
CREATE POLICY org_projects ON projects USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_sources ON sources;
CREATE POLICY org_sources ON sources USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_conversations ON conversations;
CREATE POLICY org_conversations ON conversations USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_knowledge ON knowledge_items;
CREATE POLICY org_knowledge ON knowledge_items USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_research ON research_jobs;
CREATE POLICY org_research ON research_jobs USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_learning ON learning_events;
CREATE POLICY org_learning ON learning_events USING (organization_id = current_organization_id());
DROP POLICY IF EXISTS org_audit ON audit_logs;
CREATE POLICY org_audit ON audit_logs USING (organization_id = current_organization_id());
