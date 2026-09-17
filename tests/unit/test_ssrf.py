import pytest
from app.intelligence.fetch import SafeFetcher
from app.core.errors import UnsafeExternalContentError

def test_localhost_blocked():
    with pytest.raises(UnsafeExternalContentError):
        SafeFetcher().validate_url('http://127.0.0.1:8000')
