class RetrievalService:
    def __init__(self, structured_search, semantic_search, relationship_search):
        self.structured=structured_search; self.semantic=semantic_search; self.relationships=relationship_search

    def retrieve(self, *, query: str, embedding: list[float] | None, project_id: str | None,
                 allowed_projects: set[str] | None, allowed_channels: set[str] | None, limit: int=20):
        return {'structured':self.structured(query, project_id, limit),
                'semantic':self.semantic(embedding, allowed_projects, allowed_channels, limit) if embedding else [],
                'relationships':self.relationships(query, project_id, limit)}
