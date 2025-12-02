from collections.abc import Iterable

from dishka import Provider

from app.setup.ioc.application import ApplicationProvider
from app.setup.ioc.distillation import DistillationProvider
from app.setup.ioc.domain import DomainProvider
from app.setup.ioc.infrastructure import infrastructure_provider
from app.setup.ioc.presentation import PresentationProvider
from app.setup.ioc.settings import SettingsProvider
from app.setup.ioc.agno import AgnoProvider
from app.setup.ioc.graph import GraphProvider


def get_providers() -> Iterable[Provider]:
    return (
        DomainProvider(),
        ApplicationProvider(),
        infrastructure_provider(),
        PresentationProvider(),
        SettingsProvider(),
        DistillationProvider(),
        AgnoProvider(),
        GraphProvider(),
    )
