"""
Agent Squad Infrastructure Layer Providers.

Provides infrastructure adapters and external service clients.
"""

from typing import Any
import os

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from app.domain.enums.agent_type import AgentType
from app.domain.ports.agent_squad.agent_gateway import AgentGateway
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.infrastructure.adapters.agent_squad.agent_llm_gateway import AgentLLMGateway
from app.domain.value_objects.agent_squad.agent_squad_config import (
    AgentSquadConfig,
    AgentConfig,
)
from app.infrastructure.adapters.agent_squad.context_storage_redis import (
    ContextStorageRedis,
)
from app.infrastructure.adapters.agent_squad.feature_flags_config import (
    FeatureFlagsConfig,
)
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI
from app.infrastructure.adapters.agent_squad.llm_client_vertex_ai import LLMClientVertexAI
from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra
from app.infrastructure.adapters.agent_squad.llm_client_with_fallback import LLMClientWithFallback
from app.setup.config.agent_squad import AgentSquadSettings
from app.setup.config.settings import AppSettings

# Core user-facing agents (10)
from app.infrastructure.adapters.agent_squad.agents.chat_agent_openai import (
    ChatAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.hunter_ai_agent_openai import (
    HunterAIAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.research_agent_perplexity import (
    ResearchAgentPerplexity,
)
from app.infrastructure.adapters.agent_squad.agents.execution_agent_privy import (
    ExecutionAgentPrivy,
)
from app.infrastructure.adapters.agent_squad.agents.risk_analyzer_agent_openai import (
    RiskAnalyzerAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.portfolio_agent_openai import (
    PortfolioAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.tax_optimizer_agent_openai import (
    TaxOptimizerAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.defi_yield_agent_openai import (
    DefiYieldAgentOpenAI,
)
from app.infrastructure.adapters.agent_squad.agents.security_auditor_agent_slither import (
    SecurityAuditorAgentSlither,
)
from app.infrastructure.adapters.agent_squad.agents.gas_optimizer_agent_openai import (
    GasOptimizerAgentOpenAI,
)

# Enterprise agents (4)
from app.infrastructure.adapters.agent_squad.agents.enterprise.compliance_monitor_agent_chainalysis import (
    ComplianceMonitorAgentChainalysis,
)
from app.infrastructure.adapters.agent_squad.agents.enterprise.multisig_coordinator_agent_gnosis import (
    MultiSigCoordinatorAgentGnosis,
)
from app.infrastructure.adapters.agent_squad.agents.enterprise.alert_monitoring_agent_forta import (
    AlertMonitoringAgentForta,
)
from app.infrastructure.adapters.agent_squad.agents.enterprise.crisis_manager_agent_forta import (
    CrisisManagerAgentForta,
)

# Advanced agents (4)
from app.infrastructure.adapters.agent_squad.agents.advanced.bridge_crosschain_agent_axelar import (
    BridgeCrosschainAgentAxelar,
)
from app.infrastructure.adapters.agent_squad.agents.advanced.lending_borrowing_agent_aave import (
    LendingBorrowingAgentAave,
)
from app.infrastructure.adapters.agent_squad.agents.advanced.nft_asset_manager_agent_opensea import (
    NFTAssetManagerAgentOpenSea,
)
from app.infrastructure.adapters.agent_squad.agents.advanced.dao_governance_agent_snapshot import (
    DAOGovernanceAgentSnapshot,
)


class AgentSquadInfrastructureProvider(Provider):
    """Provider for Agent Squad infrastructure layer dependencies."""

    scope = Scope.REQUEST

    @provide
    def provide_llm_client(
        self, settings: AppSettings, llm_gateway: LLMGateway
    ) -> LLMClientGateway:
        """
        Provide LLM client with automatic fallback support.

        Uses configuration from [llm_provider] section to determine:
        - Primary provider (vertex_ai, deepinfra, or openai)
        - Fallback provider (optional)
        - Model mappings for each provider
        - use_unified_gateway: If true, uses AgentLLMGateway wrapping unified LLMGateway
        """
        import logging
        from app.setup.config.loader import load_full_config, get_current_env

        logger = logging.getLogger(__name__)

        # Load raw config to access llm_provider settings
        raw_config = load_full_config(env=get_current_env())

        # Get LLM provider config (using dict access with defaults)
        llm_config = raw_config.get("llm_provider", {})
        
        # Check for unified gateway feature flag
        use_unified_gateway = llm_config.get("use_unified_gateway", False)
        
        if use_unified_gateway:
            logger.info(
                "LLM client configured: using unified AgentLLMGateway "
                "(use_unified_gateway=true)"
            )
            return AgentLLMGateway(llm_gateway=llm_gateway)
        
        # Legacy path: use provider-specific clients
        primary_provider = llm_config.get("primary_provider", "vertex_ai")
        fallback_provider = llm_config.get("fallback_provider", "deepinfra")
        enable_fallback = llm_config.get("enable_fallback", True)

        # Provider configs
        vertex_config = llm_config.get("vertex_ai", {})
        deepinfra_config = llm_config.get("deepinfra", {})
        openai_config = llm_config.get("openai", {})

        # Helper to create client based on provider name
        def create_client(provider_name: str) -> LLMClientGateway:
            if provider_name == "vertex_ai":
                # Get Vertex AI credentials from raw config
                vertex_api_key = raw_config.get("vertex_ai", {}).get("API_KEY")
                if not vertex_api_key:
                    raise ValueError("Vertex AI API_KEY not found in .secrets.toml")

                logger.info(f"Creating Vertex AI LLM client")
                return LLMClientVertexAI(
                    api_key=vertex_api_key,
                    model_mapping=vertex_config.get("model_mapping"),
                )

            elif provider_name == "deepinfra":
                # Get DeepInfra credentials from raw config
                deepinfra_api_key = raw_config.get("deepinfra", {}).get("API_KEY")
                deepinfra_base_url = raw_config.get("deepinfra", {}).get(
                    "BASE_URL", "https://api.deepinfra.com/v1/openai"
                )

                if not deepinfra_api_key:
                    raise ValueError("DeepInfra API_KEY not found in .secrets.toml")

                logger.info(f"Creating DeepInfra LLM client")
                return LLMClientDeepInfra(
                    api_key=deepinfra_api_key,
                    base_url=deepinfra_base_url,
                    model_mapping=deepinfra_config.get("model_mapping"),
                )

            elif provider_name == "openai":
                # Get OpenAI API key
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")

                logger.info(f"Creating OpenAI LLM client")
                return LLMClientOpenAI(api_key=openai_api_key)

            else:
                raise ValueError(f"Unknown LLM provider: {provider_name}")

        # Create primary client
        primary_client = create_client(primary_provider)

        # Create fallback client if enabled
        fallback_client = None
        if enable_fallback and fallback_provider:
            try:
                fallback_client = create_client(fallback_provider)
            except Exception as e:
                logger.warning(f"Could not create fallback client ({fallback_provider}): {e}")

        # Wrap with fallback logic
        if fallback_client:
            logger.info(
                f"LLM client configured: primary={primary_provider}, "
                f"fallback={fallback_provider}"
            )
            return LLMClientWithFallback(
                primary_client=primary_client,
                fallback_client=fallback_client,
                enable_fallback=enable_fallback,
            )
        else:
            logger.info(f"LLM client configured: primary={primary_provider} (no fallback)")
            return primary_client

    @provide
    def provide_agent_llm_gateway(
        self, llm_gateway: LLMGateway
    ) -> AgentLLMGateway:
        """
        Provide AgentLLMGateway for unified LLM access.
        
        This adapter wraps the unified LLMGateway to provide the dict-based
        response format expected by agents. Can be used directly or via
        the feature flag in provide_llm_client.
        """
        return AgentLLMGateway(llm_gateway=llm_gateway)

    @provide
    def provide_coingecko_client(self, settings: AgentSquadSettings) -> Any:
        """Provide CoinGecko API client if enabled."""
        if not settings.external_apis.enable_coingecko:
            return None
        
        from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient
        api_key = os.getenv("COINGECKO_API_KEY")  # Optional
        return CoinGeckoClient(api_key=api_key)
    
    @provide
    def provide_oneinch_client(self, settings: AgentSquadSettings) -> Any:
        """Provide 1inch API client if enabled."""
        if not settings.external_apis.enable_1inch:
            return None
        
        from app.infrastructure.adapters.external.oneinch_client import OneInchClient
        api_key = os.getenv("ONEINCH_API_KEY", "")
        if not api_key:
            # Log warning but don't fail - can still work with some features
            return None
        return OneInchClient(api_key=api_key)
    
    @provide
    def provide_defillama_client(self, settings: AgentSquadSettings) -> Any:
        """Provide DeFiLlama API client if enabled."""
        if not settings.external_apis.enable_defillama:
            return None
        
        from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
        return DefiLlamaClient()  # No API key required
    
    @provide
    def provide_hyperliquid_client(self, settings: AgentSquadSettings) -> Any:
        """Provide Hyperliquid API client if enabled."""
        if not settings.external_apis.enable_hyperliquid:
            return None
        
        from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient
        api_key = os.getenv("HYPERLIQUID_API_KEY")
        api_secret = os.getenv("HYPERLIQUID_API_SECRET")
        
        # Can use without keys for market data
        return HyperliquidClient(api_key=api_key, api_secret=api_secret)

    @provide(scope=Scope.APP)
    async def provide_redis_client(self) -> Redis:
        """Provide Redis async client."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return Redis.from_url(redis_url, decode_responses=True)

    @provide
    def provide_context_storage(self, redis_client: Redis) -> ContextStorageGateway:
        """Provide Redis context storage."""
        return ContextStorageRedis(redis_client=redis_client)

    @provide
    def provide_agent_squad_config(
        self, settings: AgentSquadSettings
    ) -> AgentSquadConfig:
        """Provide Agent Squad configuration from settings."""
        # Convert settings to domain value object
        agent_configs = {}
        for agent_name, agent_settings in settings.agents.model_dump().items():
            agent_type = AgentType(agent_name)
            agent_configs[agent_type] = AgentConfig(
                enabled=agent_settings["enabled"],
                model=agent_settings["model"],
                temperature=agent_settings["temperature"],
                max_tokens=agent_settings["max_tokens"],
            )

        return AgentSquadConfig(
            enabled=settings.enabled,
            intent_classification_model=settings.intent_classification_model,
            intent_confidence_threshold=settings.intent_confidence_threshold,
            fallback_agent=AgentType(settings.fallback_agent),
            enable_supervisor=settings.enable_supervisor,
            supervisor_model=settings.supervisor_model,
            supervisor_max_agents=settings.supervisor_max_agents,
            supervisor_timeout_seconds=settings.supervisor_timeout_seconds,
            conversation_history_limit=settings.conversation_history_limit,
            context_window_tokens=settings.context_window_tokens,
            max_concurrent_agents=settings.max_concurrent_agents,
            routing_timeout_seconds=settings.routing_timeout_seconds,
            execution_timeout_seconds=settings.execution_timeout_seconds,
            storage_backend=settings.storage_backend,
            storage_ttl_seconds=settings.storage_ttl_seconds,
            telemetry_enabled=settings.telemetry_enabled,
            telemetry_sample_rate=settings.telemetry_sample_rate,
            agents=agent_configs,  # Changed from agent_configs to agents
        )

    @provide
    def provide_feature_flags(
        self, config: AgentSquadConfig
    ) -> FeatureFlagsGateway:
        """Provide feature flags gateway."""
        return FeatureFlagsConfig(config=config)

    # ========================================
    # Core User-Facing Agents (10)
    # ========================================

    @provide
    def provide_chat_agent(self, llm_client: LLMClientGateway) -> ChatAgentOpenAI:
        """Provide Chat agent."""
        return ChatAgentOpenAI(llm_client=llm_client)

    @provide
    def provide_hunter_ai_agent(
        self,
        llm_client: LLMClientGateway,
        coingecko_client: Any,
    ) -> HunterAIAgentOpenAI:
        """Provide Hunter AI agent with optional CoinGecko integration."""
        return HunterAIAgentOpenAI(
            llm_client=llm_client,
            coingecko_client=coingecko_client,
        )

    @provide
    def provide_research_agent(
        self,
        llm_client: LLMClientGateway,
        settings: AppSettings,
    ) -> ResearchAgentPerplexity:
        """
        Provide Research agent with optional Perplexity integration.
        
        If Perplexity is enabled and API key is available, injects PerplexityMCPServer
        for real-time web search with citations.
        """
        import os
        from app.infrastructure.mcp.servers.perplexity_mcp import PerplexityMCPServer
        from app.setup.config.mcp import MCPSettings
        
        perplexity_client = None
        
        # Check if Perplexity is enabled and API key is available
        if settings.mcp and settings.mcp.servers.perplexity_enabled:
            perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
            if perplexity_api_key:
                try:
                    # Create Perplexity MCP server
                    mcp_settings = MCPSettings(
                        enabled=True,
                        retry=settings.mcp.retry if settings.mcp else None,
                    )
                    perplexity_client = PerplexityMCPServer(
                        api_key=perplexity_api_key,
                        settings=mcp_settings,
                    )
                except Exception:
                    # If Perplexity fails to initialize, continue without it
                    perplexity_client = None
        
        return ResearchAgentPerplexity(
            llm_client=llm_client,
            perplexity_client=perplexity_client,
        )

    @provide
    def provide_execution_agent(
        self, llm_client: LLMClientGateway, settings: AppSettings
    ) -> ExecutionAgentPrivy:
        """Provide Execution agent."""
        from unittest.mock import MagicMock

        # Mock Privy client for testing (avoids external wallet dependencies)
        privy_client = MagicMock()

        # Mock swap gateway for testing (actual implementation pending)
        swap_gateway = MagicMock()

        return ExecutionAgentPrivy(
            llm_client=llm_client,
            privy_client=privy_client,
            swap_gateway=swap_gateway,
        )

    @provide
    def provide_risk_analyzer_agent(
        self, llm_client: LLMClientGateway
    ) -> RiskAnalyzerAgentOpenAI:
        """Provide Risk Analyzer agent."""
        return RiskAnalyzerAgentOpenAI(llm_client=llm_client)

    @provide
    def provide_portfolio_agent(
        self, llm_client: LLMClientGateway
    ) -> PortfolioAgentOpenAI:
        """Provide Portfolio agent."""
        return PortfolioAgentOpenAI(llm_client=llm_client)

    @provide
    def provide_tax_optimizer_agent(
        self, llm_client: LLMClientGateway
    ) -> TaxOptimizerAgentOpenAI:
        """Provide Tax Optimizer agent."""
        return TaxOptimizerAgentOpenAI(llm_client=llm_client)

    @provide
    def provide_defi_yield_agent(
        self, llm_client: LLMClientGateway
    ) -> DefiYieldAgentOpenAI:
        """Provide DeFi Yield agent."""
        return DefiYieldAgentOpenAI(llm_client=llm_client)

    @provide
    def provide_security_auditor_agent(
        self, llm_client: LLMClientGateway
    ) -> SecurityAuditorAgentSlither:
        """Provide Security Auditor agent."""
        return SecurityAuditorAgentSlither(llm_client=llm_client)

    @provide
    def provide_gas_optimizer_agent(
        self, llm_client: LLMClientGateway
    ) -> GasOptimizerAgentOpenAI:
        """Provide Gas Optimizer agent."""
        return GasOptimizerAgentOpenAI(llm_client=llm_client)

    # ========================================
    # Enterprise Agents (4)
    # ========================================

    @provide
    def provide_compliance_monitor_agent(
        self, llm_client: LLMClientGateway
    ) -> ComplianceMonitorAgentChainalysis:
        """Provide Compliance Monitor agent."""
        from unittest.mock import MagicMock
        return ComplianceMonitorAgentChainalysis(
            llm_client=llm_client,
            chainalysis_client=MagicMock(),
        )

    @provide
    def provide_multisig_coordinator_agent(
        self, llm_client: LLMClientGateway
    ) -> MultiSigCoordinatorAgentGnosis:
        """Provide Multi-Sig Coordinator agent."""
        from unittest.mock import MagicMock
        return MultiSigCoordinatorAgentGnosis(
            llm_client=llm_client,
            gnosis_safe_client=MagicMock(),
        )

    @provide
    def provide_alert_monitoring_agent(
        self, llm_client: LLMClientGateway
    ) -> AlertMonitoringAgentForta:
        """Provide Alert Monitoring agent."""
        from unittest.mock import MagicMock
        return AlertMonitoringAgentForta(
            llm_client=llm_client,
            forta_client=MagicMock(),
            twilio_client=MagicMock(),
        )

    @provide
    def provide_crisis_manager_agent(
        self, llm_client: LLMClientGateway
    ) -> CrisisManagerAgentForta:
        """Provide Crisis Manager agent."""
        from unittest.mock import MagicMock
        return CrisisManagerAgentForta(
            llm_client=llm_client,
            forta_client=MagicMock(),
            execution_client=MagicMock(),
        )

    # ========================================
    # Advanced Agents (4)
    # ========================================

    @provide
    def provide_bridge_crosschain_agent(
        self, llm_client: LLMClientGateway
    ) -> BridgeCrosschainAgentAxelar:
        """Provide Bridge Crosschain agent."""
        from unittest.mock import MagicMock
        return BridgeCrosschainAgentAxelar(
            llm_client=llm_client,
            axelar_client=MagicMock(),
        )

    @provide
    def provide_lending_borrowing_agent(
        self, llm_client: LLMClientGateway
    ) -> LendingBorrowingAgentAave:
        """Provide Lending Borrowing agent."""
        from unittest.mock import MagicMock
        return LendingBorrowingAgentAave(
            llm_client=llm_client,
            aave_client=MagicMock(),
        )

    @provide
    def provide_nft_asset_manager_agent(
        self, llm_client: LLMClientGateway
    ) -> NFTAssetManagerAgentOpenSea:
        """Provide NFT Asset Manager agent."""
        from unittest.mock import MagicMock
        return NFTAssetManagerAgentOpenSea(
            llm_client=llm_client,
            opensea_client=MagicMock(),
        )

    @provide
    def provide_dao_governance_agent(
        self, llm_client: LLMClientGateway
    ) -> DAOGovernanceAgentSnapshot:
        """Provide DAO Governance agent."""
        from unittest.mock import MagicMock
        return DAOGovernanceAgentSnapshot(
            llm_client=llm_client,
            snapshot_client=MagicMock(),
        )

    # ========================================
    # Agent Registry
    # ========================================

    @provide
    def provide_agent_registry(
        self,
        # Core agents
        chat_agent: ChatAgentOpenAI,
        hunter_ai_agent: HunterAIAgentOpenAI,
        research_agent: ResearchAgentPerplexity,
        execution_agent: ExecutionAgentPrivy,
        risk_analyzer_agent: RiskAnalyzerAgentOpenAI,
        portfolio_agent: PortfolioAgentOpenAI,
        tax_optimizer_agent: TaxOptimizerAgentOpenAI,
        defi_yield_agent: DefiYieldAgentOpenAI,
        security_auditor_agent: SecurityAuditorAgentSlither,
        gas_optimizer_agent: GasOptimizerAgentOpenAI,
        # Enterprise agents
        compliance_monitor_agent: ComplianceMonitorAgentChainalysis,
        multisig_coordinator_agent: MultiSigCoordinatorAgentGnosis,
        alert_monitoring_agent: AlertMonitoringAgentForta,
        crisis_manager_agent: CrisisManagerAgentForta,
        # Advanced agents
        bridge_crosschain_agent: BridgeCrosschainAgentAxelar,
        lending_borrowing_agent: LendingBorrowingAgentAave,
        nft_asset_manager_agent: NFTAssetManagerAgentOpenSea,
        dao_governance_agent: DAOGovernanceAgentSnapshot,
    ) -> dict[AgentType, AgentGateway]:
        """
        Provide agent registry mapping agent types to implementations.
        
        This allows the orchestrator to dynamically route to any agent.
        """
        return {
            # Core agents
            AgentType.CHAT: chat_agent,
            AgentType.HUNTER_AI: hunter_ai_agent,
            AgentType.RESEARCH: research_agent,
            AgentType.EXECUTION: execution_agent,
            AgentType.RISK_ANALYZER: risk_analyzer_agent,
            AgentType.PORTFOLIO: portfolio_agent,
            AgentType.TAX_OPTIMIZER: tax_optimizer_agent,
            AgentType.DEFI_YIELD: defi_yield_agent,
            AgentType.SECURITY_AUDITOR: security_auditor_agent,
            AgentType.GAS_OPTIMIZER: gas_optimizer_agent,
            # Enterprise agents
            AgentType.COMPLIANCE_MONITOR: compliance_monitor_agent,
            AgentType.MULTISIG_COORDINATOR: multisig_coordinator_agent,
            AgentType.ALERT_MONITORING: alert_monitoring_agent,
            AgentType.CRISIS_MANAGER: crisis_manager_agent,
            # Advanced agents
            AgentType.BRIDGE_CROSSCHAIN: bridge_crosschain_agent,
            AgentType.LENDING_BORROWING: lending_borrowing_agent,
            AgentType.NFT_ASSET_MANAGER: nft_asset_manager_agent,
            AgentType.DAO_GOVERNANCE: dao_governance_agent,
        }
