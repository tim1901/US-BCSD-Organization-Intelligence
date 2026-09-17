class KnowledgePromotion:
    HUMAN_CONFIRMATION_TYPES={'major_strategic_priority','major_decision','sensitive_truth'}
    def requires_confirmation(self, knowledge_type: str) -> bool:
        return knowledge_type in self.HUMAN_CONFIRMATION_TYPES
