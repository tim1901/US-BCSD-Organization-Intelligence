from app.storage.repositories.memory import MemoryRepository
class StructuredSearch:
    def __init__(self, repo: MemoryRepository): self.repo=repo
    def project(self, project_id: str): return self.repo.get_project(project_id)
    def decisions(self, project_id: str | None=None): return self.repo.get_decisions(project_id)
    def open_questions(self, project_id: str | None=None): return self.repo.get_open_questions(project_id)
