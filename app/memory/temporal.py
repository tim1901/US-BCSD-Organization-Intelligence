from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class TemporalState:
    valid_from: datetime | None
    valid_until: datetime | None
    supersedes_id: str | None

class TemporalService:
    def is_current(self, valid_until: datetime | None) -> bool:
        return valid_until is None
