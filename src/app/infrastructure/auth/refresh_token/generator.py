import secrets


class RefreshTokenGenerator:
    def __call__(self) -> str:
        # URL-safe, ~64 chars
        return secrets.token_urlsafe(48)


