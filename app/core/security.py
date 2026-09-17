from enum import StrEnum

class AccessScope(StrEnum):
    ORGANIZATION = 'ORGANIZATION'
    PROJECT_RESTRICTED = 'PROJECT-RESTRICTED'
    CHANNEL_RESTRICTED = 'CHANNEL-RESTRICTED'
    USER_RESTRICTED = 'USER-RESTRICTED'


def scope_allows(source_scope: AccessScope, project_id: str | None, channel_id: str | None,
                 allowed_projects: set[str] | None, allowed_channels: set[str] | None) -> bool:
    if source_scope == AccessScope.ORGANIZATION:
        return True
    if source_scope == AccessScope.PROJECT_RESTRICTED:
        return bool(project_id and allowed_projects and project_id in allowed_projects)
    if source_scope == AccessScope.CHANNEL_RESTRICTED:
        return bool(channel_id and allowed_channels and channel_id in allowed_channels)
    return False
