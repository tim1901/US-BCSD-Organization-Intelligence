import hashlib,hmac,time
from app.api.routes_slack import verify_slack_signature

def test_slack_signature_roundtrip():
    body=b'{"type":"event_callback"}'
    ts=str(int(time.time()))
    secret='secret'
    base=f'v0:{ts}:{body.decode()}'.encode()
    sig='v0='+hmac.new(secret.encode(),base,hashlib.sha256).hexdigest()
    assert verify_slack_signature(body,ts,sig,secret,300)

def test_stale_signature_rejected():
    body=b'{}'; ts=str(int(time.time())-1000); secret='secret'
    base=f'v0:{ts}:{body.decode()}'.encode(); sig='v0='+hmac.new(secret.encode(),base,hashlib.sha256).hexdigest()
    assert not verify_slack_signature(body,ts,sig,secret,300)
