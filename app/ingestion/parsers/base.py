from abc import ABC, abstractmethod
from pathlib import Path

class DocumentParser(ABC):
    @abstractmethod
    def supports(self, filename: str, content_type: str | None = None) -> bool: ...
    @abstractmethod
    def parse(self, data: bytes, filename: str) -> tuple[str, dict]: ...
