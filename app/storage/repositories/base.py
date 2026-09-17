from typing import Any
from app.storage.supabase import connection

class Repository:
    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with connection(self.organization_id) as conn:
            return conn.execute(sql, params or {}).fetchall()

    def fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        with connection(self.organization_id) as conn:
            return conn.execute(sql, params or {}).fetchone()
