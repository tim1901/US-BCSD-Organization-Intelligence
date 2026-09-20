from typing import Any, Sequence
from google import genai
from google.genai import types
from app.ai.provider import AIProvider
from app.core.config import settings

class GeminiProvider(AIProvider):
    """Central Gemini boundary.

    Organizational Interactions are stateless (`store=False`). Search grounding is
    deliberately opt-in and is only called with sanitized public research input.
    """
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError('GEMINI_API_KEY is not configured')
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def interact(self, *, model: str, input_steps: Sequence[dict[str, Any]] | str,
                 system_instruction: str | None = None, response_schema: dict | None = None,
                 use_search_grounding: bool = False) -> Any:
        kwargs: dict[str, Any] = {'model': model, 'input': input_steps, 'store': False}
        if system_instruction:
            kwargs['system_instruction'] = system_instruction
        if response_schema:
            kwargs['response_format'] = {
                'type': 'text',
                'mime_type': 'application/json',
                'schema': response_schema,
            }
        if use_search_grounding:
            kwargs['tools'] = [types.Tool(google_search=types.GoogleSearch())]
        return self.client.interactions.create(**kwargs)

    def embed(self, text: str) -> list[float]:
        result = self.client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=settings.gemini_embedding_dimensions),
        )
        return list(result.embeddings[0].values)
