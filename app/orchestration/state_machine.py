VALID_TRANSITIONS={
 'created':{'queued','cancelled'},
 'queued':{'running','cancelled'},
 'running':{'waiting','completed','failed','cancelled'},
 'waiting':{'queued','cancelled'},
 'completed':set(),'failed':set(),'cancelled':set(),
}

def assert_transition(current: str, target: str):
    if target not in VALID_TRANSITIONS.get(current,set()): raise ValueError(f'Invalid job transition {current} -> {target}')
