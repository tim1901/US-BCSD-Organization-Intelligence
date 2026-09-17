from pathlib import Path
from app.core.config import settings

class ObjectStorage:
    """Server-side abstraction for private source/attachment storage.

    The first implementation keeps business logic provider-agnostic. Production can use
    Supabase Storage through its server-side API without exposing the service key to clients.
    """
    def __init__(self) -> None:
        self.bucket = settings.supabase_storage_bucket

    def validate_path(self, path: str) -> str:
        clean = Path(path)
        if clean.is_absolute() or '..' in clean.parts:
            raise ValueError('Unsafe storage path')
        return str(clean)

    def put_bytes(self, path: str, data: bytes, content_type: str) -> dict:
        return {'bucket': self.bucket, 'path': self.validate_path(path), 'content_type': content_type, 'size': len(data)}
