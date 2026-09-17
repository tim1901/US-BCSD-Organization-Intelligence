class CitationBuilder:
    def build(self, evidence: list[dict]) -> list[dict]:
        return [{'source_id':e.get('source_id'),'locator':e.get('locator',{})} for e in evidence]
