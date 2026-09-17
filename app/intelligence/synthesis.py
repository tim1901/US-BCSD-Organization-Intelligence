from app.ai.prompts.system import RESEARCH_SYSTEM
from app.ai.schemas.research import ResearchSynthesisSchema
from app.core.config import settings

class ResearchSynthesizer:
    def __init__(self, provider): self.provider=provider
    def synthesize(self, research_package: dict) -> ResearchSynthesisSchema:
        response=self.provider.interact(model=settings.gemini_research_model,
                                       input_steps=str(research_package),
                                       system_instruction=RESEARCH_SYSTEM,
                                       response_schema=ResearchSynthesisSchema.model_json_schema())
        text=getattr(response,'output_text',None) or getattr(response,'text',None)
        if not text: raise ValueError('Research synthesis returned no text')
        return ResearchSynthesisSchema.model_validate_json(text)
