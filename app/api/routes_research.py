from fastapi import APIRouter
from app.models.dto import ResearchStartRequest
router=APIRouter(prefix='/api/research', tags=['research'])
@router.post('/start')
def start_research(request: ResearchStartRequest):
    return {'status':'queued','question':request.question,'depth':request.depth}
@router.get('/{job_id}')
def get_research(job_id: str): return {'job_id':job_id,'status':'unknown'}
