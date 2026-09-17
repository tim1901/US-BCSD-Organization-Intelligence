from fastapi import APIRouter

router = APIRouter(prefix='/api/projects', tags=['projects'])

@router.get('/{project_id}')
def get_project(project_id: str):
    return {'project_id': project_id, 'status': 'lookup_required'}

@router.get('/{project_id}/context')
def get_project_context(project_id: str):
    return {'project_id': project_id, 'context': {}}
