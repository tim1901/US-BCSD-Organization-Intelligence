TRANSIENT_CODES={429,502,503}

def should_retry(status_code: int | None, error_type: str | None) -> bool:
    return status_code in TRANSIENT_CODES or error_type in {'timeout','connection_error'}

def backoff_seconds(attempt: int) -> int:
    return min(300, 2 ** max(0, attempt))
