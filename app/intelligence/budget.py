from dataclasses import dataclass
from time import monotonic

@dataclass
class ResearchBudgetGuard:
    max_seconds: int
    max_iterations: int
    max_sources: int
    max_model_calls: int
    max_output_tokens: int
    max_cost_usd: float
    started_at: float = monotonic()
    iterations: int = 0
    sources: int = 0
    model_calls: int = 0
    estimated_cost: float = 0.0
    def assert_within_budget(self):
        if monotonic()-self.started_at > self.max_seconds: raise TimeoutError('Research time budget exceeded')
        if self.iterations > self.max_iterations: raise RuntimeError('Research iteration budget exceeded')
        if self.sources > self.max_sources: raise RuntimeError('Research source budget exceeded')
        if self.model_calls > self.max_model_calls: raise RuntimeError('Research model-call budget exceeded')
        if self.estimated_cost > self.max_cost_usd: raise RuntimeError('Research cost budget exceeded')
