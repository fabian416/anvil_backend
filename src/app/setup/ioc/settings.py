from dishka import Provider, Scope, from_context, provide

from app.infrastructure.adapters.password_hasher_bcrypt import PasswordPepper
from app.infrastructure.auth.session.timer_utc import (
    AuthSessionRefreshThreshold,
    AuthSessionTtlMin,
)
from app.infrastructure.persistence_sqla.config import PostgresDsn, SqlaEngineConfig
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAlgorithm,
    JwtSecret,
)
from app.presentation.http.auth.cookie_params import CookieParams
from app.setup.config.settings import AppSettings
from app.setup.config.admin import AdminSettings
from app.setup.config.privy import PrivySettings
from app.setup.config.distillation import DistillationSettings
from app.setup.config.transaction_confirmation import TransactionConfirmationSettings


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=AppSettings)

    @provide
    def provide_postgres_dsn(self, settings: AppSettings) -> PostgresDsn:
        return PostgresDsn(settings.postgres.dsn)

    @provide
    def provide_sqla_engine_config(self, settings: AppSettings) -> SqlaEngineConfig:
        return SqlaEngineConfig(**settings.sqla.model_dump())

    @provide
    def provide_password_pepper(self, settings: AppSettings) -> PasswordPepper:
        return PasswordPepper(settings.security.password.pepper)

    @provide
    def provide_jwt_secret(self, settings: AppSettings) -> JwtSecret:
        return JwtSecret(settings.security.auth.jwt_secret)

    @provide
    def provide_jwt_algorithm(self, settings: AppSettings) -> JwtAlgorithm:
        return settings.security.auth.jwt_algorithm

    @provide
    def provide_auth_session_ttl_min(self, settings: AppSettings) -> AuthSessionTtlMin:
        return AuthSessionTtlMin(settings.security.auth.session_ttl_min)

    @provide
    def provide_auth_session_refresh_threshold(
        self,
        settings: AppSettings,
    ) -> AuthSessionRefreshThreshold:
        return AuthSessionRefreshThreshold(
            settings.security.auth.session_refresh_threshold,
        )

    @provide
    def provide_cookie_params(self, settings: AppSettings) -> CookieParams:
        return CookieParams(secure=settings.security.cookies.secure)

    @provide
    def provide_admin_settings(self, settings: AppSettings) -> AdminSettings:
        return settings.admin

    @provide
    def provide_privy_settings(self, settings: AppSettings) -> PrivySettings:
        if settings.privy is None:
            raise ValueError("Privy settings not configured. Add [privy] section to config.toml")
        return settings.privy

    @provide
    def provide_distillation_settings(self, settings: AppSettings) -> DistillationSettings:
        """
        Provide distillation settings with fail-safe defaults.
        
        If distillation section is not in config.toml, returns disabled config.
        This allows the system to start without distillation configured.
        """
        if settings.distillation is None:
            # Return default disabled settings if not configured
            from app.setup.config.distillation import (
                VertexAISettings,
                DeepInfraSettings,
                DistillationRetrySettings,
                DistillationTelemetrySettings,
            )
            return DistillationSettings(
                enabled=False,
                provider="vertex_ai",
                fallback_provider="deepinfra",
                temperature=0.3,
                max_tokens=150,
                timeout_seconds=10.0,
                vertex_ai=VertexAISettings(
                    project_id="",
                    location="us-central1",
                    model="gemini-1.5-flash",
                ),
                deepinfra=DeepInfraSettings(
                    api_key="",
                    model="meta-llama/Llama-3.2-3B-Instruct",
                    base_url="https://api.deepinfra.com/v1/openai",
                ),
                retry=DistillationRetrySettings(
                    max_retries=3,
                    retry_delay=1.0,
                ),
                telemetry=DistillationTelemetrySettings(
                    enabled=False,
                    batch_size=10,
                    flush_interval_seconds=60,
                ),
            )
        return settings.distillation

    @provide
    def provide_transaction_confirmation_settings(
        self, settings: AppSettings
    ) -> TransactionConfirmationSettings:
        """
        Provide transaction confirmation worker settings.
        
        Uses defaults from TransactionConfirmationSettings if not configured.
        """
        return settings.transaction_confirmation
