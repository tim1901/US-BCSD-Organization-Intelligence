from app.storage.supabase import connection

class SemanticSearch:
    def __init__(self, organization_id: str): self.organization_id=organization_id
    def search(self, embedding: list[float], limit: int = 10):
        # Embedding dimensionality comes from runtime configuration; the SQL function can be
        # migrated for the active model without changing application interfaces.
        with connection(self.organization_id) as conn:
            return conn.execute('select * from semantic_search(%(embedding)s, %(limit)s)', {'embedding': embedding, 'limit': limit}).fetchall()
