from app.core.roles import UserRole, role_at_least


def test_role_hierarchy():
    assert role_at_least(UserRole.ADMIN, UserRole.VIEWER)
    assert role_at_least(UserRole.CFO, UserRole.FINANCE_MANAGER)
    assert not role_at_least(UserRole.VIEWER, UserRole.CFO)


def test_role_values():
    assert UserRole.FOUNDER.value == "founder"
    assert UserRole.CFO.value == "cfo"
