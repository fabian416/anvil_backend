"""
JWT handler for the hexagonal architecture.
"""

from typing import Dict, Any, Optional
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
    JwtPayload,
)


class JwtHandler:
    """
    JWT handler for token operations.
    """

    def __init__(self, access_token_processor: JwtAccessTokenProcessor):
        self._access_token_processor = access_token_processor

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode a JWT token and return the payload.

        Args:
            token: The JWT token to decode

        Returns:
            The decoded token payload with 'auth_session_id' key

        Raises:
            Exception: If token is invalid
        """
        auth_session_id = self._access_token_processor.decode_auth_session_id(token)
        if auth_session_id is None:
            raise Exception("Invalid token: could not decode auth_session_id")
        return {"auth_session_id": auth_session_id}

    def create_token(self, user_id: str, email: str, role: str) -> str:
        """
        Create a JWT token.
        
        Args:
            user_id: The user ID
            email: The user email
            role: The user role
            
        Returns:
            The created JWT token
        """
        payload = JwtPayload(
            sub=user_id,
            email=email,
            role=role,
        )
        return self._access_token_processor.create_token(payload)

    def verify_token(self, token: str) -> bool:
        """
        Verify if a JWT token is valid.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self._access_token_processor.decode_token(token)
            return True
        except Exception:
            return False
