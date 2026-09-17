def key_for(prefix: str, *parts: str | None) -> str:
    values=[p or 'none' for p in parts]
    return prefix + ':' + ':'.join(values)
