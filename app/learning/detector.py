class LearningDetector:
    LABELS={'new_fact','correction','decision','priority_change','project_update','question','conflict','feedback','research_finding','knowledge_gap','outcome'}
    def classify(self, text: str) -> str:
        q=text.lower()
        if any(x in q for x in ['actually','correction','changed to','moved to']): return 'correction'
        if 'decided' in q or 'decision' in q: return 'decision'
        if 'question' in q or '?' in q: return 'question'
        return 'new_fact'
