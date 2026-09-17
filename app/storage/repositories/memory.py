from app.storage.repositories.base import Repository

class MemoryRepository(Repository):
    def get_project(self, project_id: str):
        return self.fetch_one('select * from projects where id=%(id)s', {'id': project_id})

    def get_open_questions(self, project_id: str | None = None):
        if project_id:
            return self.fetch_all(
                "select * from questions where project_id=%(id)s and status='open' order by priority desc, created_at desc",
                {'id': project_id},
            )
        return self.fetch_all("select * from questions where status='open' order by priority desc, created_at desc")

    def get_decisions(self, project_id: str | None = None):
        if project_id:
            return self.fetch_all(
                'select * from decisions where project_id=%(id)s order by made_at desc nulls last, created_at desc',
                {'id': project_id},
            )
        return self.fetch_all('select * from decisions order by made_at desc nulls last, created_at desc')
