class IntelligenceEngine:
    def __init__(self, planner, search, fetcher, verifier, contradiction_detector, synthesizer, budget_factory):
        self.planner=planner; self.search=search; self.fetcher=fetcher; self.verifier=verifier
        self.contradiction_detector=contradiction_detector; self.synthesizer=synthesizer; self.budget_factory=budget_factory
    def research(self, objective: str, depth: str='standard'):
        budget=self.budget_factory(); plan=self.planner.plan(objective, depth)
        sources=[]; findings=[]
        for subq in plan['subquestions']:
            budget.iterations += 1; budget.assert_within_budget()
            public=self.search.search(subq)
            findings.append({'subquestion':subq,'discovery':repr(public)})
        package={'objective':objective,'plan':plan,'sources':sources,'findings':findings}
        return self.synthesizer.synthesize(package)
