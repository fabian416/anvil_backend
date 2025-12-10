"""
Dependency Injection provider for Request Distillation Validation System.

This provider registers all components for the enterprise-grade request validation
system that preprocesses chat messages using lightweight LLMs (Vertex AI, DeepInfra).
"""
from dishka import Provider, Scope, provide, provide_all

# Domain Services
from app.domain.services.distillation.request_preprocessor import RequestPreprocessor
from app.domain.services.distillation.telemetry_collector import DistillationTelemetryCollector
from app.domain.services.distillation.prompt_injection_detector import PromptInjectionDetector

# Domain Ports
from app.domain.ports.distillator import Distillator
from app.domain.ports.distillation_telemetry_repository import DistillationTelemetryRepository

# Infrastructure - Distillation Providers
from app.infrastructure.distillation.providers.vertex_ai_distillator import VertexAIDistillator
from app.infrastructure.distillation.providers.deepinfra_distillator import DeepInfraDistillator
from app.infrastructure.distillation.response_validator import ResponseValidator

# Infrastructure - Telemetry Repository
from app.infrastructure.persistence_sqla.repositories.distillation_telemetry_repository import (
    DistillationTelemetryRepositorySqla,
)

# Application Services
from app.application.distillation.request_distillator import RequestDistillator

# Application Interactors
from app.application.distillation.get_metrics import GetDistillationMetrics
from app.application.distillation.get_provider_status import GetProviderStatus
from app.application.distillation.update_config import UpdateDistillationConfig
from app.application.distillation.get_health import GetDistillationHealth

# Configuration
from app.setup.config.distillation import DistillationSettings


class DistillationValidationProvider(Provider):
    """
    IOC Provider for Request Distillation Validation System.
    
    This provider wires up the entire distillation validation pipeline:
    1. Configuration (DistillationSettings from TOML)
    2. Domain Services (preprocessor, telemetry, injection detector)
    3. Infrastructure Adapters (Vertex AI, DeepInfra, telemetry repo)
    4. Application Services (main orchestrator)
    5. Admin Interactors (metrics, status, config, health)
    
    Scopes:
    - APP: Shared across all requests (settings, providers, orchestrator)
    - REQUEST: Per-request instances (interactors)
    """
    
    # ═══════════════════════════════════════════════════════════════
    # DOMAIN SERVICES (APP-scoped - stateless, reusable)
    # ═══════════════════════════════════════════════════════════════
    
    domain_services = provide_all(
        RequestPreprocessor,
        ResponseValidator,
        PromptInjectionDetector,
        scope=Scope.APP,
    )
    
    # ═══════════════════════════════════════════════════════════════
    # INFRASTRUCTURE - TELEMETRY (REQUEST-scoped - needs DB session)
    # ═══════════════════════════════════════════════════════════════
    
    @provide(scope=Scope.REQUEST)
    def provide_telemetry_repository(
        self,
    ) -> DistillationTelemetryRepository:
        """Provide telemetry repository (REQUEST-scoped for DB session)."""
        return DistillationTelemetryRepositorySqla()
    
    @provide(scope=Scope.APP)
    def provide_telemetry_collector(
        self,
        settings: DistillationSettings,
    ) -> DistillationTelemetryCollector:
        """
        Provide telemetry collector (APP-scoped).
        
        NOTE: Repository is injected per-request in record() method,
        so collector itself can be APP-scoped for efficiency.
        """
        return DistillationTelemetryCollector(
            enabled=settings.telemetry.enabled,
            batch_size=settings.telemetry.batch_size,
            flush_interval_seconds=settings.telemetry.flush_interval_seconds,
        )
    
    # ═══════════════════════════════════════════════════════════════
    # INFRASTRUCTURE - DISTILLATION PROVIDERS (APP-scoped)
    # ═══════════════════════════════════════════════════════════════
    
    @provide(scope=Scope.APP)
    def provide_vertex_ai_distillator(
        self,
        settings: DistillationSettings,
        preprocessor: RequestPreprocessor,
        validator: ResponseValidator,
    ) -> VertexAIDistillator:
        """Provide Vertex AI distillation provider."""
        return VertexAIDistillator(
            settings=settings.vertex_ai,
            preprocessor=preprocessor,
            validator=validator,
            max_retries=settings.retry.max_retries,
            retry_delay=settings.retry.retry_delay,
            timeout=settings.timeout_seconds,
        )
    
    @provide(scope=Scope.APP)
    def provide_deepinfra_distillator(
        self,
        settings: DistillationSettings,
        preprocessor: RequestPreprocessor,
        validator: ResponseValidator,
    ) -> DeepInfraDistillator:
        """Provide DeepInfra distillation provider."""
        return DeepInfraDistillator(
            settings=settings.deepinfra,
            preprocessor=preprocessor,
            validator=validator,
            max_retries=settings.retry.max_retries,
            retry_delay=settings.retry.retry_delay,
            timeout=settings.timeout_seconds,
        )
    
    # ═══════════════════════════════════════════════════════════════
    # APPLICATION SERVICES - MAIN ORCHESTRATOR (APP-scoped)
    # ═══════════════════════════════════════════════════════════════
    
    @provide(scope=Scope.APP)
    def provide_request_distillator(
        self,
        settings: DistillationSettings,
        vertex_ai_provider: VertexAIDistillator,
        deepinfra_provider: DeepInfraDistillator,
        telemetry_collector: DistillationTelemetryCollector,
    ) -> RequestDistillator:
        """
        Provide main request distillator (orchestrator).
        
        Wires up primary/fallback providers based on configuration.
        """
        # Select primary provider based on config
        if settings.provider == "vertex_ai":
            primary_provider = vertex_ai_provider
            fallback_provider = deepinfra_provider
        elif settings.provider == "deepinfra":
            primary_provider = deepinfra_provider
            fallback_provider = vertex_ai_provider
        else:
            # Default to Vertex AI
            primary_provider = vertex_ai_provider
            fallback_provider = deepinfra_provider
        
        return RequestDistillator(
            settings=settings,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
            telemetry_collector=telemetry_collector,
        )
    
    # ═══════════════════════════════════════════════════════════════
    # APPLICATION INTERACTORS - ADMIN (REQUEST-scoped)
    # ═══════════════════════════════════════════════════════════════
    
    admin_interactors = provide_all(
        GetDistillationMetrics,
        GetProviderStatus,
        UpdateDistillationConfig,
        GetDistillationHealth,
        scope=Scope.REQUEST,
    )
