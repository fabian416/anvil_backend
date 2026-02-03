"""
WebSocket authentication helper.

Provides authentication and authorization utilities for WebSocket connections,
following hexagonal architecture patterns by delegating to application layer
services.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, status

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.common.ports.identity_provider import IdentityProvider
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.domain.entities.user import User
from app.domain.exceptions.auth import (
    InvalidAuthorizationHeaderError,
    InvalidTokenError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)


class WebSocketAuthHelper:
    """
    WebSocket authentication helper.

    Handles token validation and user authentication for WebSocket connections
    using the hexagonal architecture's identity provider pattern.

    Usage:
        auth_helper = WebSocketAuthHelper(identity_provider, user_gateway)
        user = await auth_helper.authenticate(websocket, token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    """

    __slots__ = ("_identity_provider", "_user_gateway")

    def __init__(
        self,
        identity_provider: IdentityProvider,
        user_gateway: UserCommandGateway,
    ):
        """
        Initialize authentication helper.

        Args:
            identity_provider: Identity provider for token validation
            user_gateway: User gateway for user retrieval
        """
        self._identity_provider = identity_provider
        self._user_gateway = user_gateway

    async def authenticate_websocket(
        self,
        websocket: WebSocket,
        token: str,
    ) -> Optional[User]:
        """
        Authenticate WebSocket connection using JWT token.

        Validates token and retrieves user entity. If authentication fails,
        the WebSocket connection is NOT closed - caller is responsible for
        connection lifecycle.

        Args:
            websocket: WebSocket connection
            token: JWT authentication token

        Returns:
            User entity if authenticated, None if authentication failed
        """
        if not token or token == "null" or token == "undefined":
            logger.warning("[WS Auth] Missing or invalid token format")
            return None

        try:
            # Extract user ID from token via identity provider
            # Note: This requires setting the token in the identity provider context
            # For WebSocket, we need to manually validate the token
            user_id = await self._validate_token_and_get_user_id(token)

            if not user_id:
                logger.warning(
                    "[WS Auth] Token validation failed: no user ID extracted"
                )
                return None

            # Retrieve user from gateway
            user = await self._user_gateway.read_by_id(user_id)

            if not user:
                logger.warning(
                    f"[WS Auth] User not found for ID: {user_id}. "
                    "Token may be valid but user deleted."
                )
                return None

            logger.info(f"[WS Auth] Successfully authenticated user: {user_id}")
            return user

        except InvalidTokenError as e:
            logger.warning(f"[WS Auth] Invalid token: {e}")
            return None

        except TokenExpiredError as e:
            logger.warning(f"[WS Auth] Expired token: {e}")
            return None

        except InvalidAuthorizationHeaderError as e:
            logger.warning(f"[WS Auth] Invalid authorization header: {e}")
            return None

        except AuthorizationError as e:
            logger.warning(f"[WS Auth] Authorization error: {e}")
            return None

        except Exception as e:
            logger.error(
                f"[WS Auth] Unexpected authentication error: {e}", exc_info=True
            )
            return None

    async def _validate_token_and_get_user_id(self, token: str) -> Optional[int]:
        """
        Validate JWT token and extract user ID.

        This is a simplified implementation. In production, you should:
        1. Use the infrastructure JWT handler to validate the token
        2. Extract claims and verify signature
        3. Check expiration and other token properties

        Args:
            token: JWT token string

        Returns:
            User ID if token is valid, None otherwise

        Raises:
            InvalidTokenError: If token is malformed
            TokenExpiredError: If token has expired
        """
        # TODO: Replace with actual JWT validation using infrastructure layer
        # For now, this is a placeholder that delegates to identity provider
        #
        # In a real implementation, you would:
        # 1. Import JWTHandler from infrastructure.auth.handlers.jwt_handler
        # 2. Validate and decode the token
        # 3. Extract user_id from claims
        # 4. Return the user_id
        #
        # Example:
        # from app.infrastructure.auth.handlers.jwt_handler import JWTHandler
        # jwt_handler = JWTHandler(config)
        # claims = jwt_handler.decode_access_token(token)
        # return claims.get("user_id")

        try:
            # For now, attempt to get current user ID from identity provider
            # This assumes the identity provider has access to the token
            # through some request context (needs integration work)
            user_id = await self._identity_provider.get_current_user_id()
            return user_id
        except Exception as e:
            logger.debug(f"[WS Auth] Failed to extract user ID from token: {e}")
            return None

    async def check_conversation_access(
        self,
        user: User,
        conversation_id: UUID,
    ) -> bool:
        """
        Check if user has access to a conversation.

        This is a placeholder for conversation authorization logic.
        Should delegate to authorization service in application layer.

        Args:
            user: Authenticated user
            conversation_id: Conversation to check access for

        Returns:
            True if user has access, False otherwise
        """
        # TODO: Implement actual conversation access check
        # Should delegate to authorization service:
        #
        # from app.application.common.services.authorization import AuthorizationService
        # result = await auth_service.check_conversation_access(user.id, conversation_id)
        # return result

        # For now, assume all authenticated users have access
        return True


async def close_websocket_with_error(
    websocket: WebSocket,
    code: int,
    reason: str,
) -> None:
    """
    Close WebSocket connection with error code and reason.

    Helper function to safely close WebSocket connections with
    proper error reporting.

    Args:
        websocket: WebSocket connection
        code: WebSocket close code
        reason: Human-readable close reason
    """
    try:
        await websocket.close(code=code, reason=reason)
        logger.info(f"[WS] Closed connection: {reason} (code={code})")
    except Exception as e:
        logger.warning(f"[WS] Error closing WebSocket: {e}")
