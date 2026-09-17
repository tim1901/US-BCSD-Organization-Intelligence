class ConflictDetector:
    def detect_claim_conflicts(self, claims: list[dict]) -> list[dict]:
        conflicts=[]
        by_key={}
        for claim in claims:
            key=(claim.get('project_id'), claim.get('statement','').split(':',1)[0].strip().lower())
            if key in by_key and by_key[key].get('statement') != claim.get('statement'):
                conflicts.append({'a':by_key[key],'b':claim,'status':'open'})
            else:
                by_key[key]=claim
        return conflicts
