"""
Celery task helpers.

Common utility functions for Celery tasks.
"""

from app.setup.ioc.provider_registry import get_providers
from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings


async def _run_task(coro_factory):
    """
    Helper function to run async tasks with Dishka IOC container.

    Args:
        coro_factory: Coroutine factory that receives the container

    Returns:
        Task result
    """
    settings = load_settings()
    container = create_async_ioc_container(
        providers=(
            ApplicationProvider(),
            infrastructure_provider(),
            PresentationProvider(),
            SettingsProvider(),
        ),
        settings=settings,
    )
    try:
        # Enter request scope so REQUEST-scoped providers can be resolved
        async with container() as request_container:  # type: ignore[misc]
            return await coro_factory(request_container)
    finally:
        await container.close()
