"""
Authenticated API test client wrapper.

Provides a convenient wrapper around FastAPI TestClient with:
- Automatic authentication handling
- Session management
- Role switching (as_admin, as_user)
- Cookie and header-based auth support

Usage:
    from tests.helpers.api_client import AuthenticatedClient

    # Create client and login
    client = AuthenticatedClient(app)
    await client.login("user@example.com", "password")

    # Make authenticated requests
    response = client.get("/api/v1/account/me")

    # Switch to admin context
    with client.as_admin():
        response = client.get("/api/v1/admin/users")
"""

from contextlib import contextmanager
from typing import Any, Generator
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers.auth_helper import AuthHelper, TestUser, UserRole


class AuthenticatedClient:
    """
    Authenticated test client wrapper for FastAPI.

    Provides methods for making authenticated HTTP requests with
    automatic token management and role switching.

    Now supports async operations with httpx.AsyncClient.
    """

    def __init__(
        self,
        app: FastAPI | None = None,
        base_url: str = "http://testserver",
    ):
        """
        Initialize the authenticated client.

        Args:
            app: FastAPI application instance
            base_url: Base URL for requests
        """
        self._app = app
        self._base_url = base_url
        self._client = None  # Will be AsyncClient
        self._current_user: TestUser | None = None
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._use_cookies: bool = False
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

    def set_app(self, app: FastAPI) -> "AuthenticatedClient":
        """Set the FastAPI application for async client."""
        self._app = app
        return self

    @property
    def client(self):
        """Get the FastAPI app for AsyncClient initialization."""
        if self._app is None:
            raise ValueError("No FastAPI app set. Call set_app() first.")
        return self._app

    @property
    def current_user(self) -> TestUser | None:
        """Get the currently authenticated user."""
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        """Check if client is currently authenticated."""
        return self._access_token is not None

    def login(
        self,
        email: str | None = None,
        password: str = "TestPassword123!",
        role: UserRole = "user",
    ) -> "AuthenticatedClient":
        """
        Login with credentials or create a test user.

        If email is provided, attempts actual login.
        If email is None, creates a test user with the specified role.

        Args:
            email: User email (None to create test user)
            password: User password
            role: User role for test user creation

        Returns:
            Self for method chaining
        """
        if email is None:
            # Create a test user
            user, token = AuthHelper.create_test_user(role=role, password=password)
            self._current_user = user
            self._access_token = token
            self._refresh_token = user.refresh_token
        else:
            # Attempt actual login via API
            response = self.client.post(
                "/api/v1/account/login",
                json={"email": email, "password": password},
            )
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")
                # Create user object from response
                self._current_user = TestUser(
                    id=UUID(data.get("user", {}).get("id", str(UUID(int=0)))),
                    email=email,
                    password=password,
                    role=data.get("user", {}).get("role", "user").lower(),
                    access_token=self._access_token,
                    refresh_token=self._refresh_token,
                )
            else:
                raise ValueError(f"Login failed: {response.status_code} - {response.text}")

        self._update_headers()
        return self

    def login_as_admin(self) -> "AuthenticatedClient":
        """
        Login as an admin user.

        Creates a test admin user and authenticates.

        Returns:
            Self for method chaining
        """
        return self.login(role="admin")

    def login_as_super_admin(self) -> "AuthenticatedClient":
        """
        Login as a super admin user.

        Creates a test super admin user and authenticates.

        Returns:
            Self for method chaining
        """
        return self.login(role="super_admin")

    def logout(self) -> "AuthenticatedClient":
        """
        Logout and clear authentication state.

        Returns:
            Self for method chaining
        """
        if self._current_user and self._current_user.session_id:
            AuthHelper.invalidate_session(self._current_user.session_id)

        self._current_user = None
        self._access_token = None
        self._refresh_token = None
        self._update_headers()
        return self

    def refresh_token(self) -> "AuthenticatedClient":
        """
        Refresh the access token using the refresh token.

        Returns:
            Self for method chaining
        """
        if self._refresh_token is None:
            raise ValueError("No refresh token available")

        response = self.client.post(
            "/api/v1/account/refresh-token",
            json={"refresh_token": self._refresh_token},
        )

        if response.status_code == 200:
            data = response.json()
            self._access_token = data.get("access_token")
            if "refresh_token" in data:
                self._refresh_token = data["refresh_token"]
            self._update_headers()
        else:
            raise ValueError(f"Token refresh failed: {response.status_code}")

        return self

    def use_cookies(self, use: bool = True) -> "AuthenticatedClient":
        """
        Configure client to use cookie-based authentication.

        Args:
            use: Whether to use cookies for auth

        Returns:
            Self for method chaining
        """
        self._use_cookies = use
        self._update_headers()
        return self

    @contextmanager
    def as_admin(self) -> Generator["AuthenticatedClient", None, None]:
        """
        Context manager to temporarily switch to admin role.

        Saves current state, creates admin session, and restores
        original state on exit.

        Yields:
            Self with admin authentication
        """
        # Save current state
        saved_user = self._current_user
        saved_access_token = self._access_token
        saved_refresh_token = self._refresh_token

        try:
            # Create admin session
            self.login_as_admin()
            yield self
        finally:
            # Restore original state
            self._current_user = saved_user
            self._access_token = saved_access_token
            self._refresh_token = saved_refresh_token
            self._update_headers()

    @contextmanager
    def as_super_admin(self) -> Generator["AuthenticatedClient", None, None]:
        """
        Context manager to temporarily switch to super admin role.

        Yields:
            Self with super admin authentication
        """
        saved_user = self._current_user
        saved_access_token = self._access_token
        saved_refresh_token = self._refresh_token

        try:
            self.login_as_super_admin()
            yield self
        finally:
            self._current_user = saved_user
            self._access_token = saved_access_token
            self._refresh_token = saved_refresh_token
            self._update_headers()

    @contextmanager
    def as_user(
        self, email: str | None = None, role: UserRole = "user"
    ) -> Generator["AuthenticatedClient", None, None]:
        """
        Context manager to temporarily switch to a different user.

        Args:
            email: User email (None to create test user)
            role: User role

        Yields:
            Self with new user authentication
        """
        saved_user = self._current_user
        saved_access_token = self._access_token
        saved_refresh_token = self._refresh_token

        try:
            self.login(email=email, role=role)
            yield self
        finally:
            self._current_user = saved_user
            self._access_token = saved_access_token
            self._refresh_token = saved_refresh_token
            self._update_headers()

    @contextmanager
    def unauthenticated(self) -> Generator["AuthenticatedClient", None, None]:
        """
        Context manager to temporarily make unauthenticated requests.

        Yields:
            Self without authentication
        """
        saved_user = self._current_user
        saved_access_token = self._access_token
        saved_refresh_token = self._refresh_token

        try:
            self._access_token = None
            self._update_headers()
            yield self
        finally:
            self._current_user = saved_user
            self._access_token = saved_access_token
            self._refresh_token = saved_refresh_token
            self._update_headers()

    def _update_headers(self) -> None:
        """Update request headers based on current authentication state."""
        self._headers = {"Content-Type": "application/json"}
        if self._access_token and not self._use_cookies:
            self._headers["Authorization"] = f"Bearer {self._access_token}"

    def _get_cookies(self) -> dict[str, str] | None:
        """Get cookies for request if using cookie auth."""
        if self._use_cookies and self._access_token:
            return {"access_token": self._access_token}
        return None

    # HTTP method wrappers
    async def get(self, path: str, **kwargs) -> Any:
        """
        Make async GET request with authentication.

        Args:
            path: Request path
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=self.client), base_url=self._base_url) as ac:
            return await ac.get(
                path,
                headers={**self._headers, **kwargs.pop("headers", {})},
                cookies=self._get_cookies(),
                **kwargs,
            )

    async def post(self, path: str, json: dict | None = None, **kwargs) -> Any:
        """
        Make async POST request with authentication.

        Args:
            path: Request path
            json: JSON body
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=self.client), base_url=self._base_url) as ac:
            return await ac.post(
                path,
                json=json,
                headers={**self._headers, **kwargs.pop("headers", {})},
                cookies=self._get_cookies(),
                **kwargs,
            )

    async def put(self, path: str, json: dict | None = None, **kwargs) -> Any:
        """
        Make async PUT request with authentication.

        Args:
            path: Request path
            json: JSON body
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=self.client), base_url=self._base_url) as ac:
            return await ac.put(
                path,
                json=json,
                headers={**self._headers, **kwargs.pop("headers", {})},
                cookies=self._get_cookies(),
                **kwargs,
            )

    async def patch(self, path: str, json: dict | None = None, **kwargs) -> Any:
        """
        Make async PATCH request with authentication.

        Args:
            path: Request path
            json: JSON body
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=self.client), base_url=self._base_url) as ac:
            return await ac.patch(
                path,
                json=json,
                headers={**self._headers, **kwargs.pop("headers", {})},
                cookies=self._get_cookies(),
                **kwargs,
            )

    async def delete(self, path: str, **kwargs) -> Any:
        """
        Make async DELETE request with authentication.

        Args:
            path: Request path
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=self.client), base_url=self._base_url) as ac:
            return await ac.delete(
                path,
                headers={**self._headers, **kwargs.pop("headers", {})},
                cookies=self._get_cookies(),
                **kwargs,
            )

    def websocket_connect(self, path: str, **kwargs) -> Any:
        """
        Create WebSocket connection with authentication.

        Args:
            path: WebSocket path
            **kwargs: Additional connection arguments

        Returns:
            WebSocket connection context manager
        """
        # Add auth token to query params or headers for WebSocket
        if self._access_token:
            if "params" not in kwargs:
                kwargs["params"] = {}
            kwargs["params"]["token"] = self._access_token

        return self.client.websocket_connect(path, **kwargs)
