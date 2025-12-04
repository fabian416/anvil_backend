from pydantic import BaseModel

from app.setup.config.database import PostgresSettings, SqlaEngineSettings
from app.setup.config.loader import ValidEnvs, get_current_env, load_full_config
from app.setup.config.logs import LoggingSettings
from app.setup.config.security import SecuritySettings
from app.setup.config.mailgun import MailgunSettings
from app.setup.config.stripe import StripeSettings
from app.setup.config.privy import PrivySettings
from app.setup.config.integrations import IntegrationSettings
from app.setup.config.mcp import MCPSettings
from app.setup.config.agno import AgnoSettings


class AppSettings(BaseModel):
    postgres: PostgresSettings
    sqla: SqlaEngineSettings
    security: SecuritySettings
    logs: LoggingSettings
    mailgun: MailgunSettings | None = None
    stripe: StripeSettings | None = None
    privy: PrivySettings | None = None
    integrations: IntegrationSettings = IntegrationSettings()
    mcp: MCPSettings = MCPSettings()
    agno: AgnoSettings = AgnoSettings()


def load_settings(env: ValidEnvs | None = None) -> AppSettings:
    if env is None:
        env = get_current_env()
    raw_config = load_full_config(env=env)
    return AppSettings.model_validate(raw_config)
