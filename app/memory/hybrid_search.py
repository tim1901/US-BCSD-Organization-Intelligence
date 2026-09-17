class HybridSearch:
    def __init__(self, structured, semantic, relationships):
        self.structured=structured; self.semantic=semantic; self.relationships=relationships
    def search(self, query: str, embedding: list[float] | None, limit: int=10):
        structured=self.structured(query, limit)
        semantic=self.semantic(embedding, limit) if embedding else []
        return self._merge(structured, semantic, limit)
    @staticmethod
    def _merge(a, b, limit):
        seen=set(); out=[]
        for item in list(a)+list(b):
            key=str(item.get('id')) if isinstance(item,dict) else repr(item)
            if key not in seen:
                seen.add(key); out.append(item)
            if len(out)>=limit: break
        return out
