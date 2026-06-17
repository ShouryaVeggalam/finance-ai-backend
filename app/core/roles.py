from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    FOUNDER = "founder"
    FINANCE_MANAGER = "finance_manager"
    ACCOUNTANT = "accountant"
    CONTROLLER = "controller"
    CFO = "cfo"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.ACCOUNTANT: 1,
    UserRole.FINANCE_MANAGER: 2,
    UserRole.CONTROLLER: 3,
    UserRole.CFO: 4,
    UserRole.FOUNDER: 5,
    UserRole.ADMIN: 6,
}


def role_at_least(user_role: UserRole, required: UserRole) -> bool:
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required, 0)
