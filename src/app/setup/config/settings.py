from pydantic import BaseModel

from app.setup.config.admin import AdminSettings
from app.setup.config.agent_squad import AgentSquadSettings
from app.setup.config.agno import AgnoSettings
from app.setup.config.database import PostgresSettings, SqlaEngineSettings
from app.setup.config.distillation import DistillationSettings
from app.setup.config.etherscan import EtherscanSettings
from app.setup.config.integrations import IntegrationSettings
from app.setup.config.loader import ValidEnvs, get_current_env, load_full_config
from app.setup.config.logs import LoggingSettings
from app.setup.config.mailgun import MailgunSettings
from app.setup.config.mcp import MCPSettings
from app.setup.config.moonpay import MoonPaySettings
from app.setup.config.ox_protocol import OxProtocolSettings
from app.setup.config.privy import PrivySettings
from app.setup.config.projects import ProjectSettings
from app.setup.config.rpc import RPCSettings, WalletSettings
from app.setup.config.security import SecuritySettings
from app.setup.config.stripe import StripeSettings
from app.setup.config.transaction_confirmation import TransactionConfirmationSettings
from app.setup.config.translation import TranslationSettings


class AppSettings(BaseModel):
    postgres: PostgresSettings
    sqla: SqlaEngineSettings
    security: SecuritySettings
    logs: LoggingSettings
    admin: AdminSettings = AdminSettings()
    mailgun: MailgunSettings | None = None
    stripe: StripeSettings | None = None
    privy: PrivySettings | None = None
    moonpay: MoonPaySettings = MoonPaySettings()
    ox_protocol: OxProtocolSettings = OxProtocolSettings()
    integrations: IntegrationSettings = IntegrationSettings()
    mcp: MCPSettings = MCPSettings()
    agno: AgnoSettings = AgnoSettings()
    projects: ProjectSettings = ProjectSettings()
    distillation: DistillationSettings | None = None
    agent_squad: AgentSquadSettings = AgentSquadSettings()
    transaction_confirmation: TransactionConfirmationSettings = TransactionConfirmationSettings()
    translation: TranslationSettings = TranslationSettings()
    rpc: RPCSettings = RPCSettings()
    wallet: WalletSettings = WalletSettings()
    etherscan: EtherscanSettings = EtherscanSettings()


def load_settings(env: ValidEnvs | None = None) -> AppSettings:
    if env is None:
        env = get_current_env()
    raw_config = load_full_config(env=env)
    return AppSettings.model_validate(raw_config)
