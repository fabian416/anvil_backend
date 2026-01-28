"""
Celery task helpers.

Common utility functions for Celery tasks.
"""

from app.setup.ioc.provider_registry import get_providers
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings


async def _run_task(coro_factory):
    """
    Helper function to run async tasks with Dishka IOC container.

    Uses all registered providers from get_providers() to ensure
    all dependencies (including GraphProvider, MoneyMarketProvider, etc.)
    are available for resolution.

    Args:
        coro_factory: Coroutine factory that receives the container

    Returns:
        Task result
    """
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),  # Use all providers
        settings=settings,
    )
    try:
        # Enter request scope so REQUEST-scoped providers can be resolved
        async with container() as request_container:  # type: ignore[misc]
            return await coro_factory(request_container)
    finally:
        await container.close()
