class ResponseBuilder:
    def build(self, answer: str, citations: list[dict] | None = None) -> str:
        if not citations:
            return answer
        lines = [answer, '', 'Sources:'] + [
            f"- {c.get('title') or c.get('url') or c.get('source_id')}" for c in citations
        ]
        return "\n".join(lines)
