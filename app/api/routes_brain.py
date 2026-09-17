from fastapi import APIRouter
from app.models.dto import BrainAskRequest
from app.brain.planner import BrainPlanner

router = APIRouter(prefix='/api/brain', tags=['brain'])

@router.post('/ask')
def ask(request: BrainAskRequest):
    plan = BrainPlanner().plan(request.question, request.project_id)
    return plan.__dict__
