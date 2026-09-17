from pydantic import BaseModel, Field

class KnowledgeObjectSchema(BaseModel):
    type: str
    statement: str
    truth_class: str
    project_ref: str | None = None
    source_span: str | None = None
    confidence: float = Field(ge=0, le=1)
    metadata: dict = Field(default_factory=dict)

class ExtractionSchema(BaseModel):
    knowledge_objects: list[KnowledgeObjectSchema] = Field(default_factory=list)
