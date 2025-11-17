"""
EmailVerification entity for the hexagonal architecture.
Based on the BaseAPI EmailVerification model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.base import Entity
from app.domain.value_objects.email_verification_id import EmailVerificationId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.verification_token import VerificationToken
from app.domain.value_objects.expiration_time import ExpirationTime
from app.domain.value_objects.verification_status import VerificationStatus
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@dataclass(eq=False, kw_only=True)
class EmailVerification(Entity[EmailVerificationId]):
    """
    EmailVerification entity representing an email verification in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    token: VerificationToken
    expires_at: ExpirationTime
    is_used: VerificationStatus
    created_at: CreatedAt
    updated_at: UpdatedAt
