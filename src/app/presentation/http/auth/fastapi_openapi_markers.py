from fastapi.security import HTTPBearer

from app.presentation.http.auth.constants import (
    COOKIE_ACCESS_TOKEN_NAME,
)

bearer_scheme = HTTPBearer(auto_error=False)
