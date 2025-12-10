"""
Admin Configuration Settings

Defines admin user configuration including:
- Super admin email (USER_ADMIN)
- List of emails allowed to become admin
"""

from pydantic import BaseModel, ConfigDict, Field


class AdminSettings(BaseModel):
    """Admin user configuration."""

    model_config = ConfigDict(populate_by_name=True)

    user_admin: str = Field(
        default="",
        alias="USER_ADMIN",
        description="Email of the super admin user",
    )

    allowed_admin_emails: list[str] = Field(
        default_factory=list,
        alias="ALLOWED_ADMIN_EMAILS",
        description="List of emails that can be promoted to admin",
    )

    def is_admin_email(self, email: str) -> bool:
        """Check if an email is in the allowed admin list.

        Args:
            email: The email to check

        Returns:
            True if email is super admin or in allowed list
        """
        email_lower = email.lower()

        # Check if it's the super admin
        if self.user_admin and email_lower == self.user_admin.lower():
            return True

        # Check if in allowed list
        allowed_lower = [e.lower() for e in self.allowed_admin_emails]
        return email_lower in allowed_lower

    def is_super_admin(self, email: str) -> bool:
        """Check if an email is the super admin.

        Args:
            email: The email to check

        Returns:
            True if email is the super admin
        """
        return bool(self.user_admin and email.lower() == self.user_admin.lower())
