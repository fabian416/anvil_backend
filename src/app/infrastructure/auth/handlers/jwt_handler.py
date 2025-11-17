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
            The decoded token payload
            
        Raises:
            Exception: If token is invalid
        """
        try:
            payload = self._access_token_processor.decode_token(token)
            return payload
        except Exception as e:
            raise Exception(f"Invalid token: {str(e)}")

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
