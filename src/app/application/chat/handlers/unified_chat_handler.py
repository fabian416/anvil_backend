"""Unified chat handler for guest and authenticated users.

This module provides a single handler that serves both guest and authenticated
users through context abstraction, maximizing code reuse while supporting
different features and configurations.
"""
import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from app.domain.chat.value_objects import (
    UserContext,
    GuestContext,
    AuthenticatedContext,
    FeatureFlags,
)
from app.application.chat.commands.get_or_create_chat_user import (
    GetOrCreateChatUserCommand,
)
from app.application.chat.commands.get_or_create_chat_conversation import (
    GetOrCreateChatConversationCommand,
)
from app.application.chat.commands.create_chat_message import (
    CreateChatMessageCommand,
)
from app.infrastructure.caching.guest_cache import GuestCache

logger = logging.getLogger(__name__)


class UnifiedChatHandler:
    """
    Universal chat handler for guest and authenticated users.

    Architecture:
    - Single handler serves both user types through context abstraction
    - Context determines behavior (storage, features, rate limits)
    - Feature flags control premium access
    - Same Hunter AI core for all users
    - Shared cache maximizes hit rate

    Example:
        # Guest user
        context = GuestContext(ip_address="1.2.3.4")
        response = await handler.handle_message(content, language, context)

        # Authenticated user
        context = AuthenticatedContext(user_id=uuid, email="user@example.com")
        response = await handler.handle_message(content, language, context)
    """

    def __init__(
        self,
        # Command handlers for guest storage (optional - for backward compatibility)
        get_or_create_guest_user: Any = None,
        get_or_create_guest_conversation: Any = None,
        create_guest_message: Any = None,

        # Command handlers for authenticated storage
        get_or_create_chat_user: Optional[GetOrCreateChatUserCommand] = None,
        get_or_create_chat_conversation: Optional[GetOrCreateChatConversationCommand] = None,
        create_chat_message: Optional[CreateChatMessageCommand] = None,

        # Shared infrastructure
        cache: Any = None,  # GuestCache
        hunter_service: Any = None,  # GuestHandlerService for Hunter AI processing
    ):
        """Initialize unified chat handler.

        Args:
            get_or_create_guest_user: Guest user command handler (optional)
            get_or_create_guest_conversation: Guest conversation command (optional)
            create_guest_message: Guest message command (optional)
            get_or_create_chat_user: Authenticated user command handler
            get_or_create_chat_conversation: Authenticated conversation command
            create_chat_message: Authenticated message command
            cache: Redis cache for Hunter AI responses
            hunter_service: Hunter AI processing service
        """
        # Guest storage handlers (optional)
        self._get_or_create_guest_user = get_or_create_guest_user
        self._get_or_create_guest_conversation = get_or_create_guest_conversation
        self._create_guest_message = create_guest_message

        # Authenticated storage handlers
        self._get_or_create_chat_user = get_or_create_chat_user
        self._get_or_create_chat_conversation = get_or_create_chat_conversation
        self._create_chat_message = create_chat_message

        # Shared infrastructure
        self._cache = cache
        self._hunter_service = hunter_service

    async def handle_message(
        self,
        content: str,
        language: str,
        context: UserContext,
    ) -> dict[str, Any]:
        """
        Handle chat message for any user type.

        Flow:
        1. Validate context and get feature flags
        2. Get or create user/conversation (context-specific storage)
        3. Classify intent from message content
        4. Check if intent is allowed for user's feature flags
        5. Check cache (shared across all users)
        6. Process with Hunter AI if not cached
        7. Save message (context-specific storage)
        8. Return response

        Args:
            content: User message content
            language: Language code (en, es, pt, zh)
            context: User context (Guest or Authenticated)

        Returns:
            Dictionary with response data:
            - content: Response message
            - intent: Detected intent
            - enrichment: Hunter AI enrichment data
            - requires_registration: Whether feature requires auth
            - user_type: "guest" or "authenticated"
            - features_available: Available feature flags

        Raises:
            ValueError: If context type is not supported
        """
        logger.info(
            f"Unified chat message",
            extra={
                "user_id": context.get_user_id(),
                "is_authenticated": context.is_authenticated(),
                "language": language,
                "content_length": len(content),
            },
        )

        # 1. Get feature flags for this context
        features = FeatureFlags.from_context(context)

        # 2. Get or create conversation (storage depends on context)
        conversation_id = await self._get_or_create_conversation(
            context, language
        )

        # 3. Classify intent from content
        intent = self._classify_intent(content)

        logger.debug(
            f"Intent classified: {intent}",
            extra={"user_id": context.get_user_id(), "intent": intent},
        )

        # 3.5. Handle knowledge queries - informational responses available to ALL users
        if intent == "knowledge_query":
            logger.info(
                f"Knowledge query detected - providing informational response",
                extra={"user_id": context.get_user_id(), "content_preview": content[:50]},
            )
            
            # Generate knowledge response (available to all users, no auth required)
            knowledge_response = self._get_knowledge_response(content, language)
            
            # Save message
            message_id = await self._save_message(
                context=context,
                conversation_id=conversation_id,
                role="user",
                content=content,
                intent=intent,
                enrichment=None,
            )
            
            return {
                "message_id": message_id,
                "content": knowledge_response,
                "intent": intent,
                "enrichment": None,
                "requires_registration": False,  # Knowledge is free for all!
                "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
                "features_available": features.to_dict(),
            }

        # 4. Check if intent is allowed for user's features
        if not features.is_intent_allowed(intent):
            logger.info(
                f"Intent not allowed for user",
                extra={
                    "user_id": context.get_user_id(),
                    "intent": intent,
                    "is_authenticated": context.is_authenticated(),
                },
            )

            # Return upgrade prompt
            return {
                "message_id": str(uuid4()),
                "content": self._get_upgrade_message(intent),
                "intent": intent,
                "enrichment": None,
                "requires_registration": True,
                "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
                "features_available": features.to_dict(),
            }

        # 5. Extract token from content
        token = self._extract_token(content) or "BTC"

        # 6. Check cache (shared across all users)
        cached = await self._cache.get_hunter_response(
            intent, token, language
        )

        if cached:
            logger.debug(
                f"Cache HIT",
                extra={
                    "user_id": context.get_user_id(),
                    "intent": intent,
                    "token": token,
                },
            )

            # Save message from cache
            message_id = await self._save_message(
                context=context,
                conversation_id=conversation_id,
                role="user",
                content=content,
                intent=intent,
                enrichment=cached.get("enrichment"),
            )

            return {
                "message_id": message_id,
                "content": cached.get("content"),
                "intent": intent,
                "enrichment": cached.get("enrichment"),
                "requires_registration": False,
                "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
                "features_available": features.to_dict(),
            }

        # 7. Process with Hunter AI (cache miss)
        logger.debug(
            f"Cache MISS - processing with Hunter AI",
            extra={
                "user_id": context.get_user_id(),
                "intent": intent,
                "token": token,
            },
        )

        response = await self._hunter_service.process_intent(
            intent=intent,
            token=token,
            language=language,
            content=content,
            is_authenticated=context.is_authenticated(),
        )

        # 8. Cache response (shared)
        await self._cache.set_hunter_response(
            intent, token, language, response
        )

        # 9. Save message
        message_id = await self._save_message(
            context=context,
            conversation_id=conversation_id,
            role="user",
            content=content,
            intent=intent,
            enrichment=response.get("enrichment"),
        )

        return {
            "message_id": message_id,
            "content": response.get("content"),
            "intent": intent,
            "enrichment": response.get("enrichment"),
            "requires_registration": False,
            "user_type": "guest" if isinstance(context, GuestContext) else "authenticated",
            "features_available": features.to_dict(),
        }

    async def _get_or_create_conversation(
        self, context: UserContext, language: str
    ) -> UUID:
        """Get or create conversation based on context.

        Args:
            context: User context
            language: Language code

        Returns:
            Conversation UUID

        Raises:
            ValueError: If context type not supported
        """
        if isinstance(context, GuestContext):
            # Guest user - use guest storage
            user = await self._get_or_create_guest_user.execute(
                context.ip_address
            )

            conversation = await self._get_or_create_guest_conversation.execute(
                user.id, language
            )

            return conversation.id

        elif isinstance(context, AuthenticatedContext):
            # Authenticated user - use chat storage
            if not self._get_or_create_chat_user or not self._get_or_create_chat_conversation:
                raise NotImplementedError(
                    "Authenticated chat handlers not configured. "
                    "Ensure get_or_create_chat_user and get_or_create_chat_conversation "
                    "are provided during initialization."
                )

            # Get or create chat user (bridge to legacy users table)
            chat_user = await self._get_or_create_chat_user.execute(
                user_id=context.user_id,  # Legacy INTEGER user_id
                email=context.email,
                subscription_tier=context.subscription_tier,
            )

            # Get or create conversation
            conversation = await self._get_or_create_chat_conversation.execute(
                chat_user.id_, language
            )

            return conversation.id_

        else:
            raise ValueError(f"Unknown context type: {type(context)}")

    async def _save_message(
        self,
        context: UserContext,
        conversation_id: UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
        enrichment: Optional[dict] = None,
    ) -> str:
        """Save message to appropriate storage.

        Args:
            context: User context
            conversation_id: Conversation UUID
            role: Message role (user, assistant)
            content: Message content
            intent: Detected intent
            enrichment: Hunter AI enrichment data

        Returns:
            Message ID (string)

        Raises:
            ValueError: If context type not supported
        """
        if isinstance(context, GuestContext):
            # Guest user - use guest storage
            message = await self._create_guest_message.execute(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent=intent,
                enrichment=enrichment,
            )

            return str(message.id)

        elif isinstance(context, AuthenticatedContext):
            # Authenticated user - use chat storage
            if not self._create_chat_message:
                raise NotImplementedError(
                    "Authenticated chat message handler not configured. "
                    "Ensure create_chat_message is provided during initialization."
                )

            message = await self._create_chat_message.execute(
                conversation_id=conversation_id,
                role=role,
                content=content,
                intent=intent,
                enrichment=enrichment,
            )

            return str(message.id_)

        else:
            raise ValueError(f"Unknown context type: {type(context)}")

    def _classify_intent(self, content: str) -> str:
        """Classify intent from message content.

        Improved version that properly routes:
        - Informational queries to knowledge responses
        - Hunter AI queries to market analysis
        - DeFi action queries to appropriate handlers

        Args:
            content: User message content

        Returns:
            Intent name (hunter_sentiment, hunter_trading_signals, knowledge_query, etc.)
        """
        content_lower = content.lower()

        # Pattern matching for intent classification
        
        # INFORMATIONAL QUERIES (Knowledge Agent territory)
        # Questions about capabilities, features, "what is", "how to", "can i"
        informational_patterns = [
            # "Can I" questions about features
            "can i swap", "can i trade", "can i exchange", "can i lend", "can i deposit",
            "can i bridge", "can i buy", "can i sell", "can i send", "can i receive",
            # "What" questions about features
            "what swaps", "what type of swap", "what types of swap", "what can i swap",
            "what is anvil", "what does anvil", "what features", "what can i do",
            "what is swap", "what is lending", "what is defi",
            # "How" questions
            "how to swap", "how do i swap", "how to trade", "how to lend", "how to bridge",
            "how does swap", "how does anvil", "how do swaps work",
            # Feature explanations
            "tell me about swap", "explain swap", "show me swap", "describe swap",
            "supported tokens", "supported chains", "supported aggregators",
            # Aggregator questions
            "1inch", "hyperliquid", "uniswapx", "lifi", "moonpay", "aggregator",
        ]
        
        if any(pattern in content_lower for pattern in informational_patterns):
            return "knowledge_query"
        
        # HUNTER AI - Market analysis and sentiment
        if any(word in content_lower for word in ["sentiment", "feel", "bullish", "bearish", "mood", "market feel"]):
            return "hunter_sentiment"

        if any(word in content_lower for word in ["signal", "entry", "exit", "when to buy", "when to sell"]):
            return "hunter_trading_signals"

        if any(word in content_lower for word in ["price", "predict", "forecast", "target", "will reach"]):
            return "hunter_price_prediction"

        if any(word in content_lower for word in ["pattern", "chart", "technical", "rsi", "macd", "support", "resistance"]):
            return "hunter_patterns"

        if any(word in content_lower for word in ["portfolio", "optimize", "allocation", "rebalance", "diversify"]):
            return "hunter_portfolio"

        if any(word in content_lower for word in ["risk", "danger", "warning", "safe", "risky"]):
            return "hunter_risk_signals"

        # Default to knowledge_query for general DeFi questions instead of hunter_sentiment
        # This ensures users get helpful information rather than market sentiment analysis
        return "knowledge_query"

    def _extract_token(self, content: str) -> Optional[str]:
        """Extract cryptocurrency token from content.

        Args:
            content: User message content

        Returns:
            Token symbol (BTC, ETH, etc.) or None
        """
        content_upper = content.upper()

        # Common token symbols
        tokens = ["BTC", "ETH", "SOL", "USDT", "BNB", "USDC", "ADA", "DOT", "MATIC", "LINK"]

        for token in tokens:
            if token in content_upper:
                return token

        return None

    def _get_upgrade_message(self, intent: str) -> str:
        """Get upgrade message for locked features.

        Args:
            intent: Intent that requires upgrade

        Returns:
            User-friendly upgrade message
        """
        feature_names = {
            "hunter_patterns": "Pattern Detection",
            "hunter_portfolio": "Portfolio Optimization",
            "hunter_risk_signals": "Risk Analysis",
        }

        feature_name = feature_names.get(intent, "This feature")

        return (
            f"🔒 **{feature_name}** is a premium feature.\n\n"
            f"Sign up for free to unlock:\n"
            f"✨ Pattern Detection\n"
            f"✨ Portfolio Optimization\n"
            f"✨ Risk Analysis\n"
            f"✨ Unlimited messages\n"
            f"✨ Permanent conversation history\n\n"
            f"[Sign Up Free](https://anvil.fi/signup)"
        )

    def _get_knowledge_response(self, content: str, language: str) -> str:
        """Get knowledge-based informational response.

        Provides helpful information about Anvil's capabilities in response
        to informational queries like "can I swap?", "what swaps are available?", etc.

        Args:
            content: User's query content
            language: Language code (en, es, pt, zh)

        Returns:
            Informational response about Anvil's features
        """
        content_lower = content.lower()

        # Multi-language responses
        responses = {
            "swap": {
                "en": """✅ **Yes, you can swap tokens on Anvil!**

Anvil supports multiple swap types through leading DEX aggregators:

🔄 **Swap Options:**
• **1inch** - Best rates across 100+ DEX liquidity sources
• **Hyperliquid** - High-performance perpetual swaps (20,000+ TPS, no gas fees)
• **UniswapX** - Dutch auction-based routing for optimal prices
• **LiFi** - Cross-chain swaps and bridges across multiple networks

💱 **Supported Tokens:**
• Major tokens: BTC, ETH, USDC, USDT, DAI, SOL, MATIC, and 100+ more
• Across chains: Ethereum, Base, Arbitrum, Optimism, Polygon

🌉 **Cross-Chain Bridges:**
• Bridge tokens between Ethereum, Base, Arbitrum, Optimism, and Polygon
• Automatic bridge selection for best rates

To execute a swap, create a free account to connect your wallet securely.

👉 **Ready to swap?** Sign up at /signup""",
                "es": """✅ **¡Sí, puedes intercambiar tokens en Anvil!**

Anvil soporta múltiples tipos de swaps a través de agregadores DEX líderes:

🔄 **Opciones de Swap:**
• **1inch** - Mejores tasas en más de 100 fuentes de liquidez DEX
• **Hyperliquid** - Swaps perpetuos de alto rendimiento (20,000+ TPS, sin gas)
• **UniswapX** - Enrutamiento basado en subasta holandesa
• **LiFi** - Swaps y bridges entre cadenas

💱 **Tokens Soportados:**
• Tokens principales: BTC, ETH, USDC, USDT, DAI, SOL, MATIC y más de 100
• En cadenas: Ethereum, Base, Arbitrum, Optimism, Polygon

Para ejecutar un swap, crea una cuenta gratuita para conectar tu wallet.

👉 **¿Listo para intercambiar?** Regístrate en /signup""",
                "pt": """✅ **Sim, você pode trocar tokens na Anvil!**

Anvil suporta múltiplos tipos de swap através de agregadores DEX líderes:

🔄 **Opções de Swap:**
• **1inch** - Melhores taxas em mais de 100 fontes de liquidez DEX
• **Hyperliquid** - Swaps perpétuos de alto desempenho
• **UniswapX** - Roteamento baseado em leilão holandês
• **LiFi** - Swaps e bridges entre redes

💱 **Tokens Suportados:**
• Principais: BTC, ETH, USDC, USDT, DAI, SOL, MATIC e mais de 100
• Redes: Ethereum, Base, Arbitrum, Optimism, Polygon

Para executar um swap, crie uma conta gratuita.

👉 **Pronto para trocar?** Cadastre-se em /signup""",
                "zh": """✅ **是的，您可以在 Anvil 上交换代币！**

Anvil 通过领先的 DEX 聚合器支持多种交换类型：

🔄 **交换选项：**
• **1inch** - 100+ DEX 流动性来源的最佳费率
• **Hyperliquid** - 高性能永续交换
• **UniswapX** - 基于荷兰拍卖的路由
• **LiFi** - 跨链交换和桥接

💱 **支持的代币：**
• 主要代币：BTC、ETH、USDC、USDT、DAI、SOL、MATIC 等 100+
• 跨链：Ethereum、Base、Arbitrum、Optimism、Polygon

要执行交换，请创建免费账户连接您的钱包。

👉 **准备好交换了吗？** 在 /signup 注册""",
            },
            "lending": {
                "en": """✅ **Yes, you can lend assets on Anvil!**

Anvil supports lending (supplying assets to earn yield) through Morpho vaults:

💰 **Lending Features:**
• Supply USDC, ETH, WBTC, and other assets to earn APY
• Real-time APY data from DeFiLlama
• No lockup periods - withdraw anytime
• Optimized vault selection for best yields

📈 **Typical APY Ranges:**
• Stablecoins (USDC, USDT): 3-8% APY
• ETH: 2-5% APY
• WBTC: 1-3% APY

⚠️ **Note:** Anvil supports LENDING (supply assets to earn yield), not borrowing.

👉 **Ready to earn?** Sign up at /signup""",
                "es": """✅ **¡Sí, puedes prestar activos en Anvil!**

Anvil soporta préstamos (suministro de activos para ganar rendimiento) a través de vaults de Morpho:

💰 **Características de Préstamo:**
• Suministra USDC, ETH, WBTC y otros activos para ganar APY
• Datos de APY en tiempo real de DeFiLlama
• Sin períodos de bloqueo - retira cuando quieras

📈 **Rangos típicos de APY:**
• Stablecoins (USDC, USDT): 3-8% APY
• ETH: 2-5% APY

⚠️ **Nota:** Anvil soporta PRÉSTAMO (suministro de activos), no préstamo de activos.

👉 **¿Listo para ganar?** Regístrate en /signup""",
            },
            "anvil": {
                "en": """🔶 **Anvil - Your DeFi Command Center**

Anvil is a comprehensive DeFi platform that provides:

🔄 **Token Swaps**
• 1inch, Hyperliquid, UniswapX, LiFi aggregators
• 100+ supported tokens across 5+ chains

💰 **Lending (Earn Yield)**
• Supply assets to Morpho vaults
• Earn competitive APY on stablecoins and crypto

📊 **Portfolio Management**
• Multi-chain wallet tracking
• Real-time portfolio analytics
• Performance monitoring

🔬 **Market Intelligence**
• Hunter AI for sentiment analysis and predictions
• Real-time price tracking
• Risk assessment tools

🛡️ **Security**
• Non-custodial - you control your keys
• Smart contract security audits
• MEV protection options

👉 **Get started free:** /signup""",
            },
            "default": {
                "en": """🔶 **Anvil DeFi Platform**

Here's what you can do on Anvil:

🔄 **Swap Tokens** - Trade across 1inch, Hyperliquid, UniswapX, LiFi
💰 **Earn Yield** - Supply assets to Morpho vaults
📊 **Track Portfolio** - Multi-chain analytics and monitoring
🔬 **Market Analysis** - Hunter AI sentiment and predictions

All features require a free account to connect your wallet securely.

👉 **Get started:** /signup

What would you like to know more about?""",
                "es": """🔶 **Plataforma DeFi Anvil**

Esto es lo que puedes hacer en Anvil:

🔄 **Intercambiar Tokens** - Opera con 1inch, Hyperliquid, UniswapX, LiFi
💰 **Ganar Rendimiento** - Suministra activos a vaults de Morpho
📊 **Seguir Portafolio** - Análisis multi-cadena
🔬 **Análisis de Mercado** - Hunter AI sentimiento y predicciones

👉 **Comienza gratis:** /signup""",
                "pt": """🔶 **Plataforma DeFi Anvil**

Aqui está o que você pode fazer na Anvil:

🔄 **Trocar Tokens** - Negocie com 1inch, Hyperliquid, UniswapX, LiFi
💰 **Ganhar Rendimento** - Forneça ativos para vaults Morpho
📊 **Acompanhar Portfólio** - Análise multi-rede
🔬 **Análise de Mercado** - Hunter AI sentimento e previsões

👉 **Comece grátis:** /signup""",
                "zh": """🔶 **Anvil DeFi 平台**

这是您可以在 Anvil 上做的事情：

🔄 **交换代币** - 通过 1inch、Hyperliquid、UniswapX、LiFi 交易
💰 **赚取收益** - 向 Morpho 金库提供资产
📊 **跟踪投资组合** - 多链分析和监控
🔬 **市场分析** - Hunter AI 情绪和预测

👉 **免费开始：** /signup""",
            },
        }

        # Detect topic from content
        if any(word in content_lower for word in ["swap", "exchange", "trade token", "can i swap", "types of swap"]):
            topic_responses = responses.get("swap", responses["default"])
        elif any(word in content_lower for word in ["lend", "lending", "supply", "deposit", "earn", "yield", "apy", "morpho"]):
            topic_responses = responses.get("lending", responses["default"])
        elif any(word in content_lower for word in ["anvil", "what is anvil", "platform", "features"]):
            topic_responses = responses.get("anvil", responses["default"])
        else:
            topic_responses = responses["default"]

        # Return response in requested language, fallback to English
        return topic_responses.get(language, topic_responses.get("en", responses["default"]["en"]))
