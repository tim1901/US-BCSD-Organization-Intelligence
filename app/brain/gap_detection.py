class KnowledgeGapDetector:
    def detect(self, plan, context):
        gaps=[]
        if plan.intent=='meeting_preparation' and not context.get('memory',{}).get('decisions'): gaps.append('No decision history found for the project.')
        return gaps
