"""
Session entity for the hexagonal architecture.
Based on the BaseAPI Session model with domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.base import Entity
from app.domain.value_objects.session_id import SessionId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.access_token import AccessToken
from app.domain.value_objects.refresh_token import RefreshToken
from app.domain.value_objects.token_type import TokenType
from app.domain.value_objects.ip_address import IpAddress
from app.domain.value_objects.user_agent import UserAgent
from app.domain.value_objects.expiration_time import ExpirationTime
from app.domain.value_objects.last_activity import LastActivity
from app.domain.value_objects.session_status import SessionStatus
from app.domain.value_objects.created_at import CreatedAt


@dataclass(eq=False, kw_only=True)
class Session(Entity[SessionId]):
    """
    Session entity representing a user session in the system.
    
    This is an anemic model following DDD principles where behavior
    is handled by domain services rather than the entity itself.
    """
    user_id: UserId
    access_token: AccessToken
    refresh_token: RefreshToken
    token_type: TokenType
    ip_address: Optional[IpAddress]
    user_agent: Optional[UserAgent]
    created_at: CreatedAt
    expires_at: ExpirationTime
    last_activity: LastActivity
    is_active: SessionStatus
