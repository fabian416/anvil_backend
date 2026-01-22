"""
Agent Squad Infrastructure Layer Providers.

Provides infrastructure adapters and external service clients.
"""

from typing import Any, Protocol
import os

from dishka import Provider, Scope, provide


class DefiLlamaClientProtocol(Protocol):
    """Protocol for DefiLlamaClient to help Dishka distinguish it from other types."""
    async def get_protocol_yields(self, protocol: str | None = None, chain: str | None = None) -> Any: ...
    async def get_protocol_tvl(self, protocol: str) -> Any: ...
    async def get_all_protocols(self) -> Any: ...
    async def close(self) -> None: ...


class Web3ClientProtocol(Protocol):
    """Protocol for Web3Client to help Dishka distinguish it from other types."""
    async def get_gas_price(self) -> Any: ...
    async def get_block_number(self) -> int: ...
    async def is_connected(self) -> bool: ...


class OneInchClientProtocol(Protocol):
    """Protocol for OneInchClient to help Dishka distinguish it from other types."""
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 1.0,
    ) -> Any: ...


class LiFiClientProtocol(Protocol):
    """Protocol for LiFiClient to help Dishka distinguish it from other types."""
    async def get_quote(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str,
    ) -> Any: ...
from redis.asyncio import Redis

from app.domain.enums.agent_type import AgentType
from app.domain.ports.agent_squad.agent_gateway import AgentGateway
from app.domain.ports.agent_squad.context_storage_gateway import ContextStorageGateway
from app.domain.ports.agent_squad.feature_flags_gateway import FeatureFlagsGateway
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.compound_gateway import CompoundGateway
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
# OpenAI removed - using only Vertex AI and DeepInfra
# from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI
from app.infrastructure.adapters.agent_squad.llm_client_vertex_ai import LLMClientVertexAI
from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra
from app.infrastructure.adapters.agent_squad.llm_client_with_fallback import LLMClientWithFallback
from app.infrastructure.adapters.external.coingecko_client import CoinGeckoClient
from app.infrastructure.adapters.external.defillama_client import DefiLlamaClient
from app.setup.config.agent_squad import AgentSquadSettings
from app.setup.config.settings import AppSettings

# Core user-facing agents (11)
from app.infrastructure.adapters.agent_squad.agents.chat_agent import (
    ChatAgent,
)
from app.infrastructure.adapters.agent_squad.agents.guest_auth_agent import (
    GuestAuthAgent,
)
from app.infrastructure.adapters.agent_squad.agents.knowledge_agent import (
    KnowledgeAgent,
)
from app.infrastructure.adapters.agent_squad.agents.hunter_ai_agent import (
    HunterAIAgent,
)
from app.infrastructure.adapters.agent_squad.agents.research_agent_perplexity import (
    ResearchAgentPerplexity,
)
from app.infrastructure.adapters.agent_squad.agents.execution_agent_privy import (
    ExecutionAgentPrivy,
)
from app.infrastructure.adapters.agent_squad.agents.risk_analyzer_agent import (
    RiskAnalyzerAgent,
)
from app.infrastructure.adapters.agent_squad.agents.portfolio_agent import (
    PortfolioAgent,
)
from app.infrastructure.adapters.agent_squad.agents.tax_optimizer_agent import (
    TaxOptimizerAgent,
)
from app.infrastructure.adapters.agent_squad.agents.defi_yield_agent import (
    DefiYieldAgent,
)
from app.infrastructure.adapters.agent_squad.agents.security_auditor_agent_slither import (
    SecurityAuditorAgentSlither,
)
from app.infrastructure.adapters.agent_squad.agents.gas_optimizer_agent import (
    GasOptimizerAgent,
)

# Authenticated user agents
from app.infrastructure.adapters.agent_squad.agents.wallet_agent import (
    WalletAgent,
)
from app.infrastructure.adapters.agent_squad.agents.transaction_history_agent import (
    TransactionHistoryAgent,
)

# Workflow agents (multi-step operations for authenticated users)
from app.infrastructure.adapters.agent_squad.agents.workflows import (
    SwapWorkflowAgent,
    LendingWorkflowAgent,
    TransferWorkflowAgent,
    BuyWorkflowAgent,
    MoneyMarketWorkflowAgent,
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
        - Primary provider (vertex_ai or deepinfra) - OpenAI removed
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
        # OpenAI removed - only vertex_ai and deepinfra supported
        primary_provider = llm_config.get("primary_provider", "vertex_ai")
        if primary_provider == "openai":
            logger.warning("OpenAI provider removed. Falling back to vertex_ai.")
            primary_provider = "vertex_ai"
        
        fallback_provider = llm_config.get("fallback_provider", "deepinfra")
        if fallback_provider == "openai":
            logger.warning("OpenAI provider removed. Falling back to deepinfra.")
            fallback_provider = "deepinfra"
        
        enable_fallback = llm_config.get("enable_fallback", True)

        # Provider configs
        vertex_config = llm_config.get("vertex_ai", {})
        deepinfra_config = llm_config.get("deepinfra", {})
        # OpenAI removed - using only Vertex AI and DeepInfra

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
                # OpenAI removed - not supported anymore
                raise ValueError(
                    "OpenAI provider has been removed. "
                    "Please use 'vertex_ai' or 'deepinfra' as provider. "
                    "Update config/local/config.toml: primary_provider = 'vertex_ai'"
                )

            else:
                raise ValueError(f"Unknown LLM provider: {provider_name}. Supported: vertex_ai, deepinfra")

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
    def provide_coingecko_client(self, settings: AgentSquadSettings) -> CoinGeckoClient | None:
        """Provide CoinGecko API client if enabled."""
        if not settings.external_apis.enable_coingecko:
            return None
        
        api_key = os.getenv("COINGECKO_API_KEY")  # Optional
        return CoinGeckoClient(api_key=api_key)
    
    @provide(scope=Scope.APP)
    def provide_oneinch_client(self, settings: AgentSquadSettings) -> OneInchClientProtocol | None:
        """Provide 1inch API client if enabled."""
        if not settings.external_apis.enable_1inch:
            return None
        
        from app.infrastructure.adapters.external.oneinch_client import OneInchClient
        api_key = os.getenv("ONEINCH_API_KEY", "")
        if not api_key:
            # Log warning but don't fail - can still work with some features
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ ONEINCH_API_KEY not set - 1inch client will be None")
            return None
        return OneInchClient(api_key=api_key)
    
    @provide(scope=Scope.APP)
    def provide_lifi_client(self, settings: AgentSquadSettings) -> LiFiClientProtocol | None:
        """Provide LiFi API client for cross-chain swaps."""
        # LiFi doesn't require an API key for public endpoints
        try:
            from app.infrastructure.adapters.external.lifi_client import LiFiClient
            return LiFiClient()
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ LiFi client not available - cross-chain swaps disabled")
            return None
    
    @provide(scope=Scope.APP)
    def provide_web3_client(self, settings: AgentSquadSettings) -> Web3ClientProtocol | None:
        """Provide Web3Client for Ethereum gas prices if enabled."""
        # Web3Client requires API keys - check if available
        # Try both direct env vars and RPC_ prefixed (from .secrets.toml export)
        alchemy_key = os.getenv("ALCHEMY_API_KEY") or os.getenv("RPC_ALCHEMY_API_KEY", "")
        infura_key = os.getenv("INFURA_API_KEY") or os.getenv("RPC_INFURA_API_KEY", "")
        
        if not alchemy_key and not infura_key:
            # No RPC provider keys - return None
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("⚠️ ALCHEMY_API_KEY/RPC_ALCHEMY_API_KEY and INFURA_API_KEY/RPC_INFURA_API_KEY not set - Web3Client will be None")
            return None
        
        from app.infrastructure.adapters.external.web3_client import Web3Client, Chain
        return Web3Client(
            alchemy_api_key=alchemy_key if alchemy_key else None,
            infura_api_key=infura_key if infura_key else None,
            chain=Chain.ETHEREUM,  # Default to Ethereum for gas prices
        )
    
    @provide(scope=Scope.APP)  # APP scope - single instance shared across requests
    def provide_defillama_client(
        self, 
        settings: AgentSquadSettings
    ) -> DefiLlamaClientProtocol | None:
        """Provide DeFiLlama API client if enabled."""
        if not settings.external_apis.enable_defillama:
            return None
        
        # Import here to avoid circular dependencies
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
    def provide_chat_agent(self, llm_client: LLMClientGateway) -> ChatAgent:
        """Provide Chat agent."""
        return ChatAgent(llm_client=llm_client)

    @provide
    def provide_guest_auth_agent(self, llm_client: LLMClientGateway) -> GuestAuthAgent:
        """Provide Guest Auth agent for handling authentication requirements."""
        return GuestAuthAgent(llm_client=llm_client)
    
    @provide
    def provide_knowledge_agent(self, llm_client: LLMClientGateway) -> KnowledgeAgent:
        """Provide Knowledge Anvil agent for educational queries and Anvil knowledge."""
        return KnowledgeAgent(llm_client=llm_client)

    @provide
    def provide_hunter_ai_agent(
        self,
        llm_client: LLMClientGateway,
        coingecko_client: CoinGeckoClient | None,  # Type-annotated for explicit DI resolution
        settings: AgentSquadSettings,
    ) -> HunterAIAgent:
        """Provide Hunter AI agent with optional CoinGecko and Hyperliquid integration."""
        # Get Hyperliquid client for spot swap quotes
        hyperliquid_client = None
        if settings.external_apis.enable_hyperliquid:
            try:
                from app.infrastructure.adapters.external.hyperliquid_client import HyperliquidClient
                hyperliquid_client = HyperliquidClient(testnet=False)
                import logging
                logging.getLogger(__name__).info("✅ Hyperliquid client enabled for Hunter AI swap quotes")
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"⚠️ Failed to create Hyperliquid client: {e}")
        
        return HunterAIAgent(
            llm_client=llm_client,
            coingecko_client=coingecko_client,
            hyperliquid_client=hyperliquid_client,
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
        self,
        llm_client: LLMClientGateway,
        settings: AppSettings,
        oneinch_client: OneInchClientProtocol | None,  # Injected from provide_oneinch_client
    ) -> ExecutionAgentPrivy:
        """Provide Execution agent with optional OneInch integration."""
        from unittest.mock import MagicMock

        # Mock Privy client for testing (avoids external wallet dependencies)
        privy_client = MagicMock()

        # Mock swap gateway for testing (actual implementation pending)
        swap_gateway = MagicMock()

        return ExecutionAgentPrivy(
            llm_client=llm_client,
            privy_client=privy_client,
            swap_gateway=swap_gateway,
            oneinch_client=oneinch_client,
        )

    @provide
    def provide_risk_analyzer_agent(
        self,
        llm_client: LLMClientGateway,
        defi_llama_client: DefiLlamaClientProtocol | None,  # Injected from provide_defillama_client
    ) -> RiskAnalyzerAgent:
        """Provide Risk Analyzer agent with optional DeFiLlama integration."""
        return RiskAnalyzerAgent(
            llm_client=llm_client,
            defi_llama_client=defi_llama_client,
        )

    @provide
    def provide_portfolio_agent(
        self,
        llm_client: LLMClientGateway,
        coingecko_client: CoinGeckoClient | None,  # Injected from provide_coingecko_client
    ) -> PortfolioAgent:
        """Provide Portfolio agent with optional CoinGecko integration."""
        return PortfolioAgent(
            llm_client=llm_client,
            coingecko_client=coingecko_client,
        )

    @provide
    def provide_tax_optimizer_agent(
        self, llm_client: LLMClientGateway
    ) -> TaxOptimizerAgent:
        """Provide Tax Optimizer agent."""
        return TaxOptimizerAgent(llm_client=llm_client)

    @provide
    def provide_defi_yield_agent(
        self,
        llm_client: LLMClientGateway,
        defi_llama_client: DefiLlamaClientProtocol | None,  # Injected from provide_defillama_client
    ) -> DefiYieldAgent:
        """Provide DeFi Yield agent with optional DeFiLlama integration."""
        return DefiYieldAgent(
            llm_client=llm_client,
            defi_llama_client=defi_llama_client,
        )

    @provide
    def provide_security_auditor_agent(
        self, llm_client: LLMClientGateway
    ) -> SecurityAuditorAgentSlither:
        """Provide Security Auditor agent."""
        return SecurityAuditorAgentSlither(llm_client=llm_client)

    @provide
    def provide_gas_optimizer_agent(
        self,
        llm_client: LLMClientGateway,
        web3_client: Web3ClientProtocol | None,  # Injected from provide_web3_client
    ) -> GasOptimizerAgent:
        """
        Provide Gas Optimizer agent with optional Web3Client integration.
        """
        return GasOptimizerAgent(
            llm_client=llm_client,
            web3_client=web3_client,
        )

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
    # Authenticated User Agents (requires login)
    # ========================================

    @provide
    def provide_wallet_agent(
        self, llm_client: LLMClientGateway
    ) -> WalletAgent:
        """
        Provide Wallet Agent for authenticated users.
        
        This agent handles wallet queries:
        - List connected wallets
        - Show balances
        - Wallet status and provider info
        """
        return WalletAgent(llm_client=llm_client)

    @provide
    def provide_transaction_history_agent(
        self, llm_client: LLMClientGateway
    ) -> TransactionHistoryAgent:
        """
        Provide Transaction History Agent for authenticated users.
        
        This agent handles transaction queries:
        - View recent transactions
        - Filter by chain/type/date
        - Volume analytics
        - Activity summaries
        """
        return TransactionHistoryAgent(llm_client=llm_client)

    # ========================================
    # Workflow Agents (multi-step operations)
    # ========================================

    @provide
    def provide_swap_workflow_agent(
        self,
        llm_client: LLMClientGateway,
        oneinch_client: OneInchClientProtocol | None,
        lifi_client: LiFiClientProtocol | None,
    ) -> SwapWorkflowAgent:
        """
        Provide Swap Workflow Agent for authenticated users.
        
        This agent handles multi-step swap operations:
        1. Parse swap request (tokens, amount)
        2. Fetch quotes from 1inch/LiFi
        3. Confirm with user
        4. Generate execute_data for frontend
        
        Integrations:
        - 1inch: Same-chain swaps
        - LiFi: Cross-chain swaps
        """
        return SwapWorkflowAgent(
            llm_client=llm_client,
            oneinch_client=oneinch_client,
            lifi_client=lifi_client,
        )

    @provide
    def provide_lending_workflow_agent(
        self,
        llm_client: LLMClientGateway,
        morpho_gateway: MorphoGateway,
        aave_gateway: AaveGateway,
    ) -> LendingWorkflowAgent:
        """
        Provide Lending Workflow Agent for authenticated users.
        
        This agent handles multi-step deposit/yield operations:
        1. Parse deposit request (asset, amount)
        2. Fetch best vault from Morpho (fallback to Aave)
        3. Show quote with APY and earnings projection
        4. Generate execute_data for frontend
        
        Integrations:
        - Morpho: MetaMorpho vaults on Base
        - Aave: Aave V3 markets as fallback
        """
        return LendingWorkflowAgent(
            llm_client=llm_client,
            morpho_gateway=morpho_gateway,
            aave_gateway=aave_gateway,
        )

    @provide
    def provide_transfer_workflow_agent(
        self,
        llm_client: LLMClientGateway,
    ) -> TransferWorkflowAgent:
        """
        Provide Transfer Workflow Agent for authenticated users.
        
        This agent handles multi-step token transfer operations:
        1. Parse transfer request (token, amount, recipient)
        2. Validate recipient address format
        3. Show transfer review and wait for confirmation
        4. Generate execute_data for frontend
        
        Features:
        - Multi-chain address validation (EVM, Solana)
        - Network detection from address format
        - User modification support
        """
        return TransferWorkflowAgent(llm_client=llm_client)

    @provide
    def provide_buy_workflow_agent(
        self,
        llm_client: LLMClientGateway,
    ) -> BuyWorkflowAgent:
        """
        Provide Buy Workflow Agent for authenticated users.
        
        This agent handles multi-step crypto purchase operations:
        1. Parse buy request (crypto, fiat amount, currency)
        2. Validate supported assets
        3. Show purchase review and wait for confirmation
        4. Generate execute_data for Privy modal
        
        Integrations:
        - Privy SDK for MoonPay/Coinbase on-ramp
        """
        return BuyWorkflowAgent(llm_client=llm_client)

    @provide
    def provide_money_market_workflow_agent(
        self,
        llm_client: LLMClientGateway,
        aave_gateway: AaveGateway,
        compound_gateway: CompoundGateway,
        morpho_gateway: MorphoGateway,
        defillama_client: DefiLlamaClientProtocol | None,
    ) -> MoneyMarketWorkflowAgent:
        """
        Provide Money Market Workflow Agent for authenticated users.
        
        This agent handles multi-step rate comparison operations:
        1. Parse comparison request (asset)
        2. Fetch rates from Aave, Compound, Morpho
        3. Show comparison with best recommendation
        4. Allow user to select protocol for deposit
        
        Integrations:
        - Aave V3 for lending markets
        - Compound V3 for lending markets
        - Morpho for vault rates
        - DeFiLlama for fallback APY data
        """
        return MoneyMarketWorkflowAgent(
            llm_client=llm_client,
            aave_gateway=aave_gateway,
            compound_gateway=compound_gateway,
            morpho_gateway=morpho_gateway,
            defillama_client=defillama_client,
        )

    # ========================================
    # Agent Registry
    # ========================================

    @provide
    def provide_agent_registry(
        self,
        # Core agents
        chat_agent: ChatAgent,
        guest_auth_agent: GuestAuthAgent,
        knowledge_agent: KnowledgeAgent,
        hunter_ai_agent: HunterAIAgent,
        research_agent: ResearchAgentPerplexity,
        execution_agent: ExecutionAgentPrivy,
        risk_analyzer_agent: RiskAnalyzerAgent,
        portfolio_agent: PortfolioAgent,
        tax_optimizer_agent: TaxOptimizerAgent,
        defi_yield_agent: DefiYieldAgent,
        security_auditor_agent: SecurityAuditorAgentSlither,
        gas_optimizer_agent: GasOptimizerAgent,
        # Authenticated user agents
        wallet_agent: WalletAgent,
        transaction_history_agent: TransactionHistoryAgent,
        # Workflow agents
        swap_workflow_agent: SwapWorkflowAgent,
        lending_workflow_agent: LendingWorkflowAgent,
        transfer_workflow_agent: TransferWorkflowAgent,
        buy_workflow_agent: BuyWorkflowAgent,
        money_market_workflow_agent: MoneyMarketWorkflowAgent,
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
            AgentType.GUEST_AUTH: guest_auth_agent,
            AgentType.KNOWLEDGE: knowledge_agent,
            AgentType.HUNTER_AI: hunter_ai_agent,
            AgentType.RESEARCH: research_agent,
            AgentType.EXECUTION: execution_agent,
            AgentType.RISK_ANALYZER: risk_analyzer_agent,
            AgentType.PORTFOLIO: portfolio_agent,
            AgentType.TAX_OPTIMIZER: tax_optimizer_agent,
            AgentType.DEFI_YIELD: defi_yield_agent,
            AgentType.SECURITY_AUDITOR: security_auditor_agent,
            AgentType.GAS_OPTIMIZER: gas_optimizer_agent,
            # Authenticated user agents
            AgentType.WALLET: wallet_agent,
            AgentType.TRANSACTION_HISTORY: transaction_history_agent,
            # Workflow agents
            AgentType.SWAP_WORKFLOW: swap_workflow_agent,
            AgentType.LENDING_WORKFLOW: lending_workflow_agent,
            AgentType.TRANSFER_WORKFLOW: transfer_workflow_agent,
            AgentType.BUY_WORKFLOW: buy_workflow_agent,
            AgentType.MONEY_MARKET_WORKFLOW: money_market_workflow_agent,
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
