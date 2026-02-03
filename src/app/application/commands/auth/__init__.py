"""
Auth commands module for the hexagonal architecture.
"""

from .upgrade_to_admin import UpgradeToAdminInteractor, UpgradeToAdminRequest
from .change_role import ChangeRoleInteractor, ChangeRoleRequest

__all__ = [
    "UpgradeToAdminInteractor",
    "UpgradeToAdminRequest",
    "ChangeRoleInteractor",
    "ChangeRoleRequest",
]
