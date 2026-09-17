CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  normalized_name TEXT, organization_type TEXT, website TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS programs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, description TEXT,
  status TEXT NOT NULL DEFAULT 'active', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS people (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, normalized_name TEXT,
  organization_id UUID REFERENCES organizations(id), role TEXT, title TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, slug TEXT, description TEXT,
  status TEXT NOT NULL DEFAULT 'active', program_id UUID REFERENCES programs(id), owner_person_id UUID REFERENCES people(id),
  current_summary TEXT, start_date DATE, end_date DATE, organization_id UUID NOT NULL REFERENCES organizations(id),
  access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION', access_scope_ref TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS organizational_priorities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, description TEXT, status TEXT NOT NULL DEFAULT 'candidate',
  priority_level TEXT, valid_from TIMESTAMPTZ, valid_until TIMESTAMPTZ, supersedes_priority_id UUID REFERENCES organizational_priorities(id),
  source_id UUID, confidence NUMERIC(5,4), confirmed_by TEXT, confirmed_at TIMESTAMPTZ,
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_type TEXT NOT NULL, external_id TEXT, url TEXT,
  storage_path TEXT, title TEXT, author TEXT, publisher TEXT, published_at TIMESTAMPTZ, captured_at TIMESTAMPTZ,
  content_hash TEXT, access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION', access_scope_ref TEXT,
  organization_id UUID NOT NULL REFERENCES organizations(id), metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_sources_hash ON sources(organization_id, content_hash) WHERE content_hash IS NOT NULL;
CREATE TABLE IF NOT EXISTS source_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  document_type TEXT NOT NULL, raw_text TEXT, structured_content JSONB NOT NULL DEFAULT '{}'::jsonb,
  parser_version TEXT, language TEXT, extraction_status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS source_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_document_id UUID NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL, chunk_text TEXT NOT NULL, source_span TEXT, locator JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding VECTOR, embedding_model TEXT, embedding_version TEXT, embedding_dimensions INTEGER, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(source_document_id, chunk_index)
);
CREATE TABLE IF NOT EXISTS slack_installations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workspace_id TEXT UNIQUE NOT NULL, workspace_name TEXT, installer_user_id TEXT,
  bot_user_id TEXT, bot_token_encrypted_ref TEXT, signing_secret_ref TEXT, scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
  installed_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ, status TEXT NOT NULL DEFAULT 'active', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS slack_channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), workspace_id TEXT NOT NULL, channel_id TEXT NOT NULL, channel_name TEXT,
  visibility TEXT, private BOOLEAN NOT NULL DEFAULT FALSE, enabled_for_ingestion BOOLEAN NOT NULL DEFAULT TRUE,
  enabled_for_interaction BOOLEAN NOT NULL DEFAULT TRUE, project_id UUID REFERENCES projects(id),
  last_backfilled_at TIMESTAMPTZ, last_event_ts TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(workspace_id, channel_id)
);
CREATE TABLE IF NOT EXISTS identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), person_id UUID REFERENCES people(id), provider TEXT NOT NULL,
  external_user_id TEXT NOT NULL, workspace_id TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(provider, external_user_id, workspace_id)
);
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), source_id UUID REFERENCES sources(id), channel_id TEXT, thread_external_id TEXT,
  conversation_type TEXT, started_at TIMESTAMPTZ, ended_at TIMESTAMPTZ,
  access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION', access_scope_ref TEXT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(channel_id, thread_external_id)
);
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  external_message_id TEXT, author_person_id UUID REFERENCES people(id), content TEXT, message_ts TIMESTAMPTZ,
  reply_to_message_id UUID REFERENCES messages(id), raw_payload JSONB, access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION',
  access_scope_ref TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(conversation_id, external_message_id)
);
CREATE TABLE IF NOT EXISTS meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES projects(id), title TEXT NOT NULL,
  start_at TIMESTAMPTZ, end_at TIMESTAMPTZ, location TEXT, agenda TEXT, status TEXT NOT NULL DEFAULT 'scheduled',
  source_id UUID REFERENCES sources(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES projects(id), statement TEXT NOT NULL,
  rationale TEXT, status TEXT NOT NULL DEFAULT 'active', made_at TIMESTAMPTZ, supersedes_decision_id UUID REFERENCES decisions(id),
  source_id UUID REFERENCES sources(id), confidence NUMERIC(5,4), confirmed_by TEXT, confirmed_at TIMESTAMPTZ,
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES projects(id), question TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open', priority INTEGER NOT NULL DEFAULT 0, first_observed_at TIMESTAMPTZ,
  last_observed_at TIMESTAMPTZ, resolved_at TIMESTAMPTZ, resolution_summary TEXT, source_id UUID REFERENCES sources(id),
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES projects(id), title TEXT NOT NULL, description TEXT,
  owner_person_id UUID REFERENCES people(id), due_at TIMESTAMPTZ, status TEXT NOT NULL DEFAULT 'open', source_id UUID REFERENCES sources(id),
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), name TEXT NOT NULL, normalized_name TEXT, parent_topic_id UUID REFERENCES topics(id),
  status TEXT NOT NULL DEFAULT 'active', organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), entity_type TEXT NOT NULL, name TEXT NOT NULL, normalized_name TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb, organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS knowledge_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), knowledge_type TEXT NOT NULL, statement TEXT NOT NULL,
  project_id UUID REFERENCES projects(id), status TEXT NOT NULL DEFAULT 'candidate', truth_class TEXT NOT NULL,
  confidence NUMERIC(5,4), valid_from TIMESTAMPTZ, valid_until TIMESTAMPTZ, source_id UUID REFERENCES sources(id),
  source_span TEXT, access_scope TEXT NOT NULL DEFAULT 'ORGANIZATION', access_scope_ref TEXT,
  created_by_type TEXT NOT NULL DEFAULT 'system', organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS knowledge_relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), from_type TEXT NOT NULL, from_id UUID NOT NULL,
  relationship_type TEXT NOT NULL, to_type TEXT NOT NULL, to_id UUID NOT NULL, confidence NUMERIC(5,4), source_id UUID REFERENCES sources(id),
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS knowledge_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), knowledge_item_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
  previous_value JSONB, new_value JSONB, change_type TEXT NOT NULL, source_id UUID REFERENCES sources(id), changed_by_type TEXT NOT NULL,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS conflicts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), object_type TEXT NOT NULL, object_id UUID NOT NULL, field_name TEXT,
  value_a JSONB, value_b JSONB, source_a_id UUID REFERENCES sources(id), source_b_id UUID REFERENCES sources(id),
  status TEXT NOT NULL DEFAULT 'open', likely_current_value JSONB, resolution_notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), resolved_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), object_type TEXT NOT NULL, object_id UUID NOT NULL, chunk_text TEXT NOT NULL,
  embedding VECTOR, embedding_model TEXT NOT NULL, embedding_version TEXT, embedding_dimensions INTEGER, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  organization_id UUID NOT NULL REFERENCES organizations(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
