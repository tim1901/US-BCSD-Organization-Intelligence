class ProjectContextService:
    def __init__(self, memory): self.memory=memory
    def get(self, project_id): return self.memory.project_context(project_id)
