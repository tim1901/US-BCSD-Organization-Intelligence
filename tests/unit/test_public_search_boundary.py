import pytest
from app.intelligence.search import PublicSearch
from app.core.errors import ValidationError

class Provider: pass

def test_private_content_blocked():
    with pytest.raises(ValidationError):
        PublicSearch(Provider()).sanitize_public_query('BEGIN CONFIDENTIAL\nsecret')
