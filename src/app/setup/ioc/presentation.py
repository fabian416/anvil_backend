from dishka import Provider, Scope, from_context, provide_all
from starlette.requests import Request

from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
)
from app.presentation.http.auth.refresh_token_processor_jwt import (
    JwtRefreshTokenProcessor,
)


class PresentationProvider(Provider):
    scope = Scope.REQUEST

    request = from_context(provides=Request)

    # Concrete Objects
    presentation_objects = provide_all(
        JwtAccessTokenProcessor,
        JwtRefreshTokenProcessor,
    )
