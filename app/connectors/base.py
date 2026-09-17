from abc import ABC, abstractmethod
from typing import Any
class Connector(ABC):
    @abstractmethod
    def health(self) -> dict[str, Any]: ...
