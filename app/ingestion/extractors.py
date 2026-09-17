from app.ai.gemini import GeminiProvider
from app.ai.prompts.system import EXTRACTION_SYSTEM
from app.ai.schemas.extraction import ExtractionSchema
from app.core.config import settings

class KnowledgeExtractor:
    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    def extract(self, content: str) -> ExtractionSchema:
        response = self.provider.interact(model=settings.gemini_fast_model,
                                          input_steps=content,
                                          system_instruction=EXTRACTION_SYSTEM,
                                          response_schema=ExtractionSchema.model_json_schema())
        # Provider response representations may vary; this placeholder expects the SDK to expose text.
        text = getattr(response, 'output_text', None) or getattr(response, 'text', None)
        if not text:
            raise ValueError('Gemini extraction returned no text output')
        return ExtractionSchema.model_validate_json(text)
