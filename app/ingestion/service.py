from hashlib import sha256
from app.ingestion.extractors import KnowledgeExtractor
from app.models.domain import NormalizedInput

class IngestionService:
    def __init__(self, extractor: KnowledgeExtractor | None = None):
        self.extractor = extractor or KnowledgeExtractor()

    def content_hash(self, item: NormalizedInput) -> str:
        return sha256(item.content.encode('utf-8')).hexdigest()

    def parse_and_extract(self, item: NormalizedInput):
        return self.extractor.extract(item.content)
