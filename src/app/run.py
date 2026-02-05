import os
from pathlib import Path

from dishka import Provider
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.presentation.http.controllers.root_router import create_root_router
from app.setup.app_factory import configure_app, create_app, create_async_ioc_container
from app.setup.config.loader import get_current_env
from app.setup.config.logs import configure_logging
from app.setup.config.settings import AppSettings, load_settings
from app.setup.ioc.provider_registry import get_providers


def _load_env_file() -> None:
    """Load environment variables from .env.{APP_ENV} file if it exists."""
    app_env = os.getenv("APP_ENV", "local")
    # Find project root (where config/ directory is)
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / "config" / app_env / f".env.{app_env}"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
            break


# Load env file on module import
_load_env_file()


def make_app(
    *di_providers: Provider,
    settings: AppSettings | None = None,
) -> FastAPI:
    if settings is None:
        configure_logging()
        settings = load_settings()

    configure_logging(level=settings.logs.level)

    app: FastAPI = create_app()
    
    # Get current environment for CORS configuration
    # This ensures CORS allows correct origins based on APP_ENV (local/dev/staging/prod)
    current_env = get_current_env()
    
    configure_app(
        app=app, 
        root_router=create_root_router(),
        environment=current_env  # ✅ Pass actual environment from APP_ENV
    )

    async_ioc_container = create_async_ioc_container(
        providers=(*get_providers(), *di_providers),
        settings=settings,
    )
    setup_dishka(container=async_ioc_container, app=app)

    return app


# NOTE: Do NOT create app at module level with `app = make_app()`
# uvicorn with --factory flag will call make_app() itself.
# Creating app at module level causes double initialization and slow startup.


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app=make_app(),
        port=8000,
        reload=False,
        loop="uvloop",
    )
