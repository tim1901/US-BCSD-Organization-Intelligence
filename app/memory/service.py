class MemoryService:
    def __init__(self, repo, retrieval): self.repo=repo; self.retrieval=retrieval
    def project_context(self, project_id):
        return {'project':self.repo.get_project(project_id),
                'decisions':self.repo.get_decisions(project_id),
                'open_questions':self.repo.get_open_questions(project_id)}
    def search(self, query, embedding=None, project_id=None, allowed_projects=None, allowed_channels=None):
        return self.retrieval.retrieve(query=query, embedding=embedding, project_id=project_id,
                                       allowed_projects=allowed_projects, allowed_channels=allowed_channels)
