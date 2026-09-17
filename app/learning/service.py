class LearningService:
    def __init__(self, detector, feedback, promotion): self.detector=detector; self.feedback=feedback; self.promotion=promotion
    def process_message(self, text): return {'learning_type':self.detector.classify(text)}
