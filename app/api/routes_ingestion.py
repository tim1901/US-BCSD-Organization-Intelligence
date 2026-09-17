from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.dto import IngestTextRequest
from app.ingestion.normalizer import normalize_text
from app.ingestion.classifiers import classify_filename

router=APIRouter(prefix='/api/ingest', tags=['ingestion'])
@router.post('/text')
def ingest_text(request: IngestTextRequest):
    item=normalize_text(request.content, source_type=request.source_type, title=request.title,
                        project_id=request.project_id, access_scope=request.access_scope)
    return {'status':'accepted','content_length':len(item.content)}

@router.post('/file')
async def ingest_file(file: UploadFile=File(...)):
    if not file.filename: raise HTTPException(status_code=400, detail='Filename required')
    kind=classify_filename(file.filename)
    if kind=='unknown': raise HTTPException(status_code=415, detail='Unsupported file type')
    data=await file.read()
    return {'status':'accepted','filename':file.filename,'type':kind,'bytes':len(data)}

@router.post('/url')
def ingest_url(url: str):
    return {'status':'accepted','url':url}
