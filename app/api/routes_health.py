from fastapi import APIRouter
router=APIRouter(tags=['health'])
@router.get('/health')
def health(): return {'status':'ok'}
@router.get('/health/dependencies')
def dependencies(): return {'database':'not_checked','gemini':'configured' if False else 'config_required','slack':'config_required'}
