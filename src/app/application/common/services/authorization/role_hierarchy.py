from collections.abc import Mapping
from typing import Final

from app.domain.enums.user_role import UserRole

SUBORDINATE_ROLES: Final[Mapping[UserRole, set[UserRole]]] = {
    # ADMIN can manage ALL roles including other ADMINs
    UserRole.ADMIN: {UserRole.ADMIN, UserRole.MODERATOR, UserRole.USER, UserRole.GUEST},
    UserRole.MODERATOR: {UserRole.USER, UserRole.GUEST},
    UserRole.USER: {UserRole.GUEST},
    UserRole.GUEST: set(),
}
