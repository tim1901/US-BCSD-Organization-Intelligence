from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from app.core.config import settings

_pool: ConnectionPool | None = None

def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        if not settings.database_url:
            raise RuntimeError('DATABASE_URL is not configured')
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={'row_factory': dict_row},
            open=True,
        )
    return _pool

@contextmanager
def connection(organization_id: str | None = None):
    with get_pool().connection() as conn:
        with conn.transaction():
            if organization_id:
                conn.execute("select set_config('app.current_organization_id', %s, true)", (organization_id,))
            yield conn
