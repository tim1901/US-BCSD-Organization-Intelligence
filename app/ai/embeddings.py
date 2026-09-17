from app.ai.gemini import GeminiProvider

class EmbeddingService:
    def __init__(self, provider: GeminiProvider | None = None):
        self.provider = provider or GeminiProvider()

    def embed(self, text: str) -> list[float]:
        return self.provider.embed(text)
