from abc import ABC, abstractmethod
from typing import Any, Sequence

class AIProvider(ABC):
    @abstractmethod
    def interact(self, *, model: str, input_steps: Sequence[dict[str, Any]] | str,
                 system_instruction: str | None = None, response_schema: dict | None = None,
                 use_search_grounding: bool = False) -> Any:
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
