from fastapi import APIRouter
router=APIRouter(prefix='/api/admin', tags=['admin'])
@router.post('/reindex')
def reindex(): return {'status':'queued','operation':'reindex_embeddings'}
@router.post('/backfill')
def backfill(): return {'status':'queued','operation':'backfill_slack'}
@router.get('/jobs/{job_id}')
def job(job_id: str): return {'job_id':job_id,'status':'unknown'}
