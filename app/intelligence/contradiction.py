class ContradictionDetector:
    def compare(self, claims: list[dict]) -> list[dict]:
        conflicts=[]
        for i,a in enumerate(claims):
            for b in claims[i+1:]:
                if a.get('topic') and a.get('topic')==b.get('topic') and a.get('value')!=b.get('value'):
                    conflicts.append({'a':a,'b':b})
        return conflicts
