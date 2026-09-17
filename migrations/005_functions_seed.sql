CREATE OR REPLACE FUNCTION semantic_search(query_embedding vector, match_count integer DEFAULT 10)
RETURNS TABLE(id uuid, object_type text, object_id uuid, chunk_text text, similarity double precision)
LANGUAGE sql STABLE AS $$
  SELECT e.id, e.object_type, e.object_id, e.chunk_text,
         1 - (e.embedding <=> query_embedding) AS similarity
  FROM embeddings e
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
$$;

INSERT INTO organizations(slug,name,normalized_name)
VALUES('us-bcsd','United States Business Council for Sustainable Development','united states business council for sustainable development')
ON CONFLICT(slug) DO NOTHING;
