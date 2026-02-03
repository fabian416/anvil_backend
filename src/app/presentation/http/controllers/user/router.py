"""
User Routes Aggregator.

All user-facing endpoints are mounted under /api/v1/user/

Structure:
- /api/v1/user/chat - Chat & conversations
- /api/v1/user/wallet - Wallet operations
- /api/v1/user/portfolio - Portfolio management
- /api/v1/user/markets - Market data
- /api/v1/user/alerts - Price alerts
- /api/v1/user/preferences - User preferences
- /api/v1/user/dashboard - User dashboard
- /api/v1/user/search - Search functionality
- /api/v1/user/comparison - Asset comparison
- /api/v1/user/notifications - Notifications
- /api/v1/user/projects - User projects
"""

from fastapi import APIRouter


def create_user_router() -> APIRouter:
    """Create the aggregated user router."""
    router = APIRouter(
        prefix="/user",
        tags=["User"],
    )

    # Import routers here to avoid circular imports
    from app.presentation.http.controllers.chat.router import create_chat_router
    from app.presentation.http.controllers.chat.analytics_dashboard import (
        router as chat_analytics_router,
    )
    from app.presentation.http.controllers.wallet.router import create_wallet_router
    from app.presentation.http.controllers.portfolio.router import (
        create_portfolio_router,
    )
    from app.presentation.http.controllers.markets.router import create_markets_router
    from app.presentation.http.controllers.alerts.router import create_alerts_router
    from app.presentation.http.controllers.preferences.router import (
        create_preferences_router,
    )
    from app.presentation.http.controllers.dashboard.router import (
        create_dashboard_router,
    )
    from app.presentation.http.controllers.search.router import create_search_router
    from app.presentation.http.controllers.comparison.router import (
        create_comparison_router,
    )
    from app.presentation.http.controllers.notification.router import (
        create_notification_router,
    )
    from app.presentation.http.controllers.user.projects_router import (
        router as projects_user_router,
    )

    # Hunter AI routers
    from app.presentation.http.controllers.hunter.sentiment import (
        create_sentiment_router,
    )
    from app.presentation.http.controllers.hunter.price_prediction import (
        create_price_prediction_router,
    )
    from app.presentation.http.controllers.hunter.risk_analysis import (
        create_risk_analysis_router,
    )
    from app.presentation.http.controllers.hunter.trading_signals import (
        create_trading_signals_router,
    )
    from app.presentation.http.controllers.hunter.patterns import create_patterns_router

    # ULTRA routers
    from app.presentation.http.controllers.ultra.flash_loans import (
        create_flash_loans_router,
    )
    from app.presentation.http.controllers.ultra.arbitrage import (
        create_arbitrage_router,
    )
    from app.presentation.http.controllers.ultra.mev import create_mev_router
    from app.presentation.http.controllers.ultra.auto_executor import (
        create_auto_executor_router,
    )

    # Graph routers (visualization + GraphRAG)
    from app.presentation.http.controllers.graph.visualization import (
        create_graph_visualization_router,
    )
    from app.presentation.http.controllers.graph import (
        search_router,
        analytics_router,
        monitoring_router,
    )

    # ML routers
    from app.presentation.http.controllers.ml import prediction_router, network_router

    # Metrics router
    from app.presentation.http.controllers.metrics.router import (
        router as metrics_router,
    )

    # WebSocket routers
    from app.presentation.http.websocket.chat_websocket import (
        router as agno_chat_ws_router,
    )
    from app.presentation.http.websocket.graph_websocket import (
        router as graph_ws_router,
    )

    # DeFi routers
    from app.presentation.http.controllers.defi.aave_router import create_aave_router
    from app.presentation.http.controllers.defi.axelar_router import (
        create_axelar_router,
    )
    from app.presentation.http.controllers.defi.curve_router import create_curve_router
    from app.presentation.http.controllers.defi.hyperliquid_router import (
        create_hyperliquid_router,
    )
    from app.presentation.http.controllers.defi.layerzero_router import (
        create_layerzero_router,
    )
    from app.presentation.http.controllers.defi.morpho_router import (
        create_morpho_router,
    )

    # NFT routers
    from app.presentation.http.controllers.nft.opensea_router import (
        create_opensea_router,
    )

    # Include all user routers
    router.include_router(create_chat_router())
    router.include_router(chat_analytics_router)
    router.include_router(create_wallet_router())
    router.include_router(create_portfolio_router())
    router.include_router(create_markets_router())
    router.include_router(create_alerts_router())
    router.include_router(create_preferences_router())
    router.include_router(create_dashboard_router())
    router.include_router(create_search_router())
    router.include_router(create_comparison_router())
    router.include_router(create_notification_router())
    router.include_router(projects_user_router)

    # Hunter AI routes
    router.include_router(create_sentiment_router())
    router.include_router(create_price_prediction_router())
    router.include_router(create_risk_analysis_router())
    router.include_router(create_trading_signals_router())
    router.include_router(create_patterns_router())
    # Note: Hunter portfolio router has type issues - using main portfolio router instead

    # ULTRA routes
    router.include_router(create_flash_loans_router())
    router.include_router(create_arbitrage_router())
    router.include_router(create_mev_router())
    router.include_router(create_auto_executor_router())

    # Graph routes (visualization + GraphRAG)
    router.include_router(create_graph_visualization_router())
    router.include_router(search_router)
    router.include_router(analytics_router)
    router.include_router(monitoring_router)

    # ML routes
    router.include_router(prediction_router)
    router.include_router(network_router)

    # Metrics routes
    router.include_router(metrics_router)

    # WebSocket routes
    router.include_router(agno_chat_ws_router)
    router.include_router(graph_ws_router)

    # DeFi routes
    router.include_router(create_aave_router(), prefix="/defi")
    router.include_router(create_axelar_router(), prefix="/defi")
    router.include_router(create_curve_router(), prefix="/defi")
    router.include_router(create_hyperliquid_router(), prefix="/defi")
    router.include_router(create_layerzero_router(), prefix="/defi")
    router.include_router(create_morpho_router(), prefix="/defi")

    # NFT routes
    router.include_router(create_opensea_router(), prefix="/nft")

    return router
