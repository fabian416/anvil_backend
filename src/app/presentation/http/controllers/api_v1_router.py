from fastapi import APIRouter

from app.presentation.http.controllers.account.router import create_account_router
from app.presentation.http.controllers.general.router import create_general_router
from app.presentation.http.controllers.admin.user.router import create_users_router
from app.presentation.http.controllers.atlas.router import create_atlas_router
from app.presentation.http.controllers.subscription.router import create_subscription_router
from app.presentation.http.controllers.notification.router import create_notification_router
from app.presentation.http.controllers.payment.router import create_payment_router
from app.presentation.http.controllers.auth.router import create_auth_router
from app.presentation.http.controllers.metrics.router import router as metrics_router
from app.presentation.http.controllers.chat.router import create_chat_router
from app.presentation.http.controllers.chat.websocket_router import create_chat_websocket_router
from app.presentation.http.controllers.admin.stats.router import create_admin_stats_router
from app.presentation.http.controllers.admin.agent.router import create_admin_agent_router
from app.presentation.http.controllers.wallet.router import create_wallet_router
from app.presentation.http.controllers.graph.visualization import create_graph_visualization_router
from app.presentation.http.controllers.hunter.sentiment import create_sentiment_router
from app.presentation.http.controllers.hunter.price_prediction import create_price_prediction_router
from app.presentation.http.controllers.hunter.risk_analysis import create_risk_analysis_router
from app.presentation.http.controllers.hunter.trading_signals import create_trading_signals_router
from app.presentation.http.controllers.hunter.portfolio import create_portfolio_router
from app.presentation.http.controllers.hunter.patterns import create_patterns_router
from app.presentation.http.controllers.ultra.flash_loans import create_flash_loans_router
from app.presentation.http.controllers.ultra.arbitrage import create_arbitrage_router
from app.presentation.http.controllers.ultra.mev import create_mev_router
from app.presentation.http.controllers.ultra.auto_executor import create_auto_executor_router

# New routers for distillation and projects
from app.presentation.http.controllers.admin.distillation_router import router as distillation_admin_router
from app.presentation.http.controllers.admin.distillation_validation_router import router as distillation_validation_router
from app.presentation.http.controllers.admin.projects_router import router as projects_admin_router
from app.presentation.http.controllers.user.projects_router import router as projects_user_router

# WebSocket router for real-time agent chat
from app.presentation.http.websocket.chat_websocket import router as agno_chat_ws_router

# GraphRAG routers
from app.presentation.http.controllers.graph import search_router, analytics_router, monitoring_router
from app.presentation.http.websocket.graph_websocket import router as graph_ws_router

# ML routers
from app.presentation.http.controllers.ml import prediction_router, network_router

# Portfolio router
from app.presentation.http.controllers.portfolio.router import create_portfolio_router

# Alerts router
from app.presentation.http.controllers.alerts.router import create_alerts_router

# Preferences router
from app.presentation.http.controllers.preferences.router import create_preferences_router

# Dashboard router
from app.presentation.http.controllers.dashboard.router import create_dashboard_router

# Search router
from app.presentation.http.controllers.search.router import create_search_router

# Comparison router
from app.presentation.http.controllers.comparison.router import create_comparison_router

# Markets router
from app.presentation.http.controllers.markets.router import create_markets_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/v1",
    )

    sub_routers = (
        create_account_router(),
        create_general_router(),
        create_users_router(),
        create_atlas_router(),
        create_subscription_router(),
        create_notification_router(),
        create_payment_router(),
        create_auth_router(),
        metrics_router,
        create_chat_router(),
        create_chat_websocket_router(),
        create_admin_stats_router(),
        create_admin_agent_router(),
        # Wallet router
        create_wallet_router(),
        # Graph visualization router
        create_graph_visualization_router(),
        # Hunter AI sentiment router
        create_sentiment_router(),
        # Hunter AI price prediction router
        create_price_prediction_router(),
        # Hunter AI risk analysis router
        create_risk_analysis_router(),
        # Hunter AI trading signals router
        create_trading_signals_router(),
        # Hunter AI portfolio optimizer router
        create_portfolio_router(),
        # Hunter AI pattern recognition router
        create_patterns_router(),
        # ULTRA Arbitrage flash loans router
        create_flash_loans_router(),
        # ULTRA Arbitrage discovery router
        create_arbitrage_router(),
        # ULTRA MEV protection router
        create_mev_router(),
        # ULTRA auto-executor router
        create_auto_executor_router(),
        # New distillation and projects routers
        distillation_admin_router,
        distillation_validation_router,  # Request validation system
        projects_admin_router,
        projects_user_router,
        # Real-time agent chat WebSocket
        agno_chat_ws_router,
        # GraphRAG routers
        search_router,
        analytics_router,
        monitoring_router,
        graph_ws_router,
        # ML routers
        prediction_router,
        network_router,
        # Portfolio router
        create_portfolio_router(),
        # Alerts router
        create_alerts_router(),
        # Preferences router
        create_preferences_router(),
        # Dashboard router
        create_dashboard_router(),
        # Search router
        create_search_router(),
        # Comparison router
        create_comparison_router(),
        # Markets router
        create_markets_router(),
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    return router
