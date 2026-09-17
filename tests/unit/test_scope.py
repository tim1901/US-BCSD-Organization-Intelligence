from app.core.security import AccessScope, scope_allows

def test_organization_scope_allows():
    assert scope_allows(AccessScope.ORGANIZATION, None, None, None, None)

def test_project_scope_requires_membership():
    assert not scope_allows(AccessScope.PROJECT_RESTRICTED, 'p1', None, {'p2'}, None)
    assert scope_allows(AccessScope.PROJECT_RESTRICTED, 'p1', None, {'p1'}, None)
