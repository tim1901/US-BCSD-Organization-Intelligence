import pytest
from app.orchestration.state_machine import assert_transition

def test_valid_transition(): assert_transition('queued','running')
def test_invalid_transition():
    with pytest.raises(ValueError): assert_transition('completed','running')
