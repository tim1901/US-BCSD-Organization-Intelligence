class EventClusterer:
    def cluster(self, findings: list[dict]) -> list[dict]:
        return [{'event_key':f.get('event_key') or f.get('title'), 'findings':[f]} for f in findings]
