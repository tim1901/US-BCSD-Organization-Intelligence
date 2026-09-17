from app.ai.prompts.system import BRAIN_SYSTEM
from app.core.config import settings

class ReasoningCore:
    def __init__(self, provider): self.provider=provider
    def answer(self, context: dict):
        response=self.provider.interact(model=settings.gemini_brain_model,
                                       input_steps=str(context),
                                       system_instruction=BRAIN_SYSTEM)
        return getattr(response,'output_text',None) or getattr(response,'text',None) or ''
