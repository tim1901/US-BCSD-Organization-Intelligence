class Orchestrator:
    def __init__(self, brain, jobs): self.brain=brain; self.jobs=jobs
    def route_question(self, question: str, project_id: str | None=None):
        plan=self.brain.plan(question, project_id)
        if plan.research_required:
            return {'mode':'async_research','job_id':self.jobs.enqueue_research(question,project_id,plan.research_depth or 'standard')}
        return {'mode':'sync_brain','plan':plan}
