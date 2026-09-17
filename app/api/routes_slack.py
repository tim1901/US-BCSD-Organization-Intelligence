import hashlib,hmac,json,time
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.storage.supabase import connection

router=APIRouter(tags=['slack'])

def verify_slack_signature(body: bytes, timestamp: str, signature: str, secret: str, max_age: int) -> bool:
    if not timestamp or not signature or not secret: return False
    try: ts=int(timestamp)
    except ValueError: return False
    if abs(time.time()-ts)>max_age: return False
    base=f'v0:{timestamp}:{body.decode("utf-8")}'.encode()
    expected='v0='+hmac.new(secret.encode(),base,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature)

@router.post('/api/slack/events')
async def slack_events(request: Request, x_slack_request_timestamp: str|None=Header(default=None), x_slack_signature: str|None=Header(default=None)):
    body=await request.body()
    if len(body)>settings.max_request_body_bytes: raise HTTPException(413,'Request too large')
    if not verify_slack_signature(body, x_slack_request_timestamp or '', x_slack_signature or '', settings.slack_signing_secret, settings.max_slack_event_age_seconds):
        raise HTTPException(401,'Invalid Slack signature')
    try: payload=json.loads(body)
    except json.JSONDecodeError: raise HTTPException(400,'Invalid JSON')
    if payload.get('type')=='url_verification': return JSONResponse({'challenge':payload.get('challenge','')})
    event_id=payload.get('event_id')
    if not event_id: return JSONResponse({'ok':True})
    workspace_id=settings.slack_workspace_id or payload.get('team_id','')
    payload_hash=hashlib.sha256(body).hexdigest()
    retry_num=int(request.headers.get('X-Slack-Retry-Num','0'))
    with connection() as conn:
        inserted=conn.execute("""
          INSERT INTO slack_events(event_id,workspace_id,event_type,payload_hash,received_at,retry_number,processing_status,raw_payload)
          VALUES(%(event_id)s,%(workspace_id)s,%(event_type)s,%(payload_hash)s,NOW(),%(retry)s,'received',%(payload)s::jsonb)
          ON CONFLICT(event_id) DO NOTHING RETURNING event_id
        """, {'event_id':event_id,'workspace_id':workspace_id,'event_type':payload.get('event',{}).get('type',payload.get('type','')),'payload_hash':payload_hash,'retry':retry_num,'payload':json.dumps(payload)}).fetchone()
        if inserted:
            conn.execute("""INSERT INTO jobs(id,job_type,payload,priority,status,available_at,attempts,max_attempts,idempotency_key,created_at)
                            VALUES(gen_random_uuid(),'ingest_slack_event',jsonb_build_object('slack_event_id',%(event_id)s),20,'queued',NOW(),0,%(max_attempts)s,%(key)s,NOW())
                            ON CONFLICT(idempotency_key) DO NOTHING""", {'event_id':event_id,'max_attempts':settings.job_max_attempts,'key':f'slack:event:{event_id}'})
    return JSONResponse({'ok':True})

@router.post('/api/slack/command')
def slack_command(): return {'status':'accepted'}
