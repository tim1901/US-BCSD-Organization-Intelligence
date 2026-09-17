from enum import StrEnum

class TruthClass(StrEnum):
    OBSERVED = 'observed'
    FACT = 'fact'
    INTERPRETATION = 'interpretation'
    HYPOTHESIS = 'hypothesis'
    CANDIDATE = 'candidate'

class JobStatus(StrEnum):
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    WAITING = 'waiting'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class ResearchDepth(StrEnum):
    QUICK = 'quick'
    STANDARD = 'standard'
    DEEP = 'deep'
    INVESTIGATIVE = 'investigative'

class LearningValidation(StrEnum):
    OBSERVED = 'observed'
    CANDIDATE = 'candidate'
    VALIDATED = 'validated'
    ESTABLISHED = 'established'

class FeedbackType(StrEnum):
    USEFUL = 'useful'
    INCORRECT = 'incorrect'
    INCOMPLETE = 'incomplete'
    OUTDATED = 'outdated'
    MISSING_CONTEXT = 'missing_context'
    WRONG_PROJECT = 'wrong_project'
    WRONG_SOURCE = 'wrong_source'
    TOO_SHALLOW = 'too_shallow'
