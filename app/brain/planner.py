from app.models.domain import BrainPlan
from app.brain.intent import IntentResolver


class BrainPlanner:
    def __init__(self, resolver=None):
        self.resolver = resolver or IntentResolver()

    def plan(self, question: str, project_id: str | None = None) -> BrainPlan:
        intent = self.resolver.resolve(question)["intent"]
        research = intent in {"deep_research", "competitive_analysis"}
        depth = "deep" if intent == "deep_research" else "standard" if research else None
        requirements = ["project", "decisions", "open_questions"] if project_id else ["relevant_memory"]
        if intent == "meeting_preparation":
            requirements = ["meeting", "project", "decisions", "open_questions"]
        if intent == "competitive_analysis":
            requirements = ["relevant_memory", "external_market_research"]
        return BrainPlan(
            intent=intent,
            project_id=project_id,
            context_requirements=requirements,
            research_required=research,
            research_depth=depth,
            uncertainties=[],
            answer_mode="full_research" if research else "memory_only",
        )
