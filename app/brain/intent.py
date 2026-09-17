class IntentResolver:
    def resolve(self, question: str) -> dict:
        q=question.lower()
        if 'next week' in q or 'tomorrow' in q or 'upcoming' in q: return {'intent':'upcoming_work'}
        if 'meeting' in q or 'prepare me' in q: return {'intent':'meeting_preparation'}
        if q.startswith('research ') or 'research this deeply' in q: return {'intent':'deep_research'}
        return {'intent':'organizational_question'}
