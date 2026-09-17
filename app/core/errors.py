class PlatformError(Exception):
    """Base application error."""

class AuthorizationError(PlatformError):
    pass

class ValidationError(PlatformError):
    pass

class TemporaryServiceError(PlatformError):
    pass

class UnsafeExternalContentError(PlatformError):
    pass
