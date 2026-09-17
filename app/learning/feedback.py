class FeedbackService:
    def validate(self, feedback_type: str) -> bool:
        return feedback_type in {'useful','incorrect','incomplete','outdated','missing_context','wrong_project','wrong_source','too_shallow'}
