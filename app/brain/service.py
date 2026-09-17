class BrainService:
    def __init__(self, planner, context_builder, memory, reasoning, gap_detector):
        self.planner=planner; self.context_builder=context_builder; self.memory=memory
        self.reasoning=reasoning; self.gap_detector=gap_detector
    def plan(self, question, project_id=None): return self.planner.plan(question, project_id)
    def ask(self, question, project_id=None, conversation_context=None):
        plan=self.plan(question, project_id)
        memory=self.memory.project_context(project_id) if project_id else {}
        context=self.context_builder.build(question=question, memory_context=memory,
                                           conversation_context=conversation_context)
        context['knowledge_gaps']=self.gap_detector.detect(plan, context)
        return {'plan':plan, 'answer':self.reasoning.answer(context), 'context':context}
