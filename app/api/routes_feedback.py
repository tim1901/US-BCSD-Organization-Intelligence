from fastapi import APIRouter
from app.models.dto import FeedbackRequest
from app.learning.feedback import FeedbackService

router = APIRouter(prefix='/api/feedback', tags=['feedback'])

@router.post('')
def feedback(request: FeedbackRequest):
    valid = FeedbackService().validate(request.feedback_type)
    if not valid:
        return {'status': 'rejected', 'reason': 'unsupported_feedback_type'}
    return {'status': 'accepted'}
