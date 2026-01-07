#!/usr/bin/env python3
"""
Script to get access token for a user by email using login endpoint.

Usage:
    python scripts/get_user_token_simple.py ops@anvilcrypto.com
"""

import asyncio
import sys
from httpx import AsyncClient, ASGITransport

from app.run import make_app


async def get_user_token_via_login(email: str, password: str = None) -> str | None:
    """
    Get access token by logging in the user.
    
    Args:
        email: User email address
        password: User password (if None, will try common test passwords)
        
    Returns:
        Access token or None if login fails
    """
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try login with password (if provided) or common test passwords
        test_passwords = [password] if password else ["test123", "password", "admin123"]
        
        for pwd in test_passwords:
            response = await client.post(
                "/api/v1/account/login",
                json={"email": email, "password": pwd},
            )
            
            if response.status_code == 200:
                data = response.json()
                # Try different response formats
                token = (
                    data.get("access_token") or
                    data.get("tokens", {}).get("access_token") or
                    data.get("token")
                )
                if token:
                    return token
        
        return None


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_user_token_simple.py <email> [password]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Attempting login for: {email}")
    
    token = await get_user_token_via_login(email, password)
    
    if token:
        print(f"\n✅ Access Token:")
        print(token)
        return token
    else:
        print("\n❌ Could not login. User may not exist or password is incorrect.")
        print("Note: You may need to provide the password as second argument.")
        sys.exit(1)


if __name__ == "__main__":
    token = asyncio.run(main())
