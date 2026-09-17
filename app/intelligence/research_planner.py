class ResearchPlanner:
    def plan(self, objective: str, depth: str) -> dict:
        parts=[p.strip() for p in objective.replace('?', '.').split('.') if p.strip()]
        return {'objective':objective,'depth':depth,'subquestions':parts[:8] or [objective],
                'source_strategy':['primary','official','research','reputable_industry','major_media']}
