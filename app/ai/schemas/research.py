from pydantic import BaseModel, Field

class ResearchSynthesisSchema(BaseModel):
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    verified_facts: list[str] = Field(default_factory=list)
    uncertain_claims: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    implications: list[str] = Field(default_factory=list)
    us_bcsd_relevance: list[str] = Field(default_factory=list)
    project_relevance: list[str] = Field(default_factory=list)
    opportunity_hypotheses: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)
    next_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
