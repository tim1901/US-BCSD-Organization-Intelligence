from pydantic import BaseModel, Field

class BrainPlanSchema(BaseModel):
    intent: str
    project_id: str | None = None
    context_requirements: list[str] = Field(default_factory=list)
    research_required: bool = False
    research_depth: str | None = None
    uncertainties: list[str] = Field(default_factory=list)
    answer_mode: str = 'memory_only'
