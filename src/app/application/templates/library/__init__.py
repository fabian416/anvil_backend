"""
Conversation Template Library

Pre-built conversation templates for common DeFi and portfolio management workflows.

Categories:
- Portfolio Management: Health checks, risk assessment, rebalancing, tax optimization
- DeFi Analysis: Protocol analysis, yield optimization, liquidity analysis
- Trading Strategies: Entry/exit strategies, position sizing, DCA builders
"""

# Portfolio Management Templates
from app.application.templates.library.portfolio.portfolio_health_check import (
    create_portfolio_health_check_template,
)
from app.application.templates.library.portfolio.risk_assessment_report import (
    create_risk_assessment_report_template,
)
from app.application.templates.library.portfolio.yield_optimization_analysis import (
    create_yield_optimization_analysis_template,
)
from app.application.templates.library.portfolio.rebalancing_recommendations import (
    create_rebalancing_recommendations_template,
)
from app.application.templates.library.portfolio.tax_loss_harvesting import (
    create_tax_loss_harvesting_template,
)

# DeFi Analysis Templates
from app.application.templates.library.defi.protocol_deep_dive import (
    create_protocol_deep_dive_template,
)
from app.application.templates.library.defi.risk_vs_reward_comparison import (
    create_risk_vs_reward_comparison_template,
)
from app.application.templates.library.defi.smart_contract_security_analysis import (
    create_smart_contract_security_analysis_template,
)
from app.application.templates.library.defi.liquidity_analysis import (
    create_liquidity_analysis_template,
)
from app.application.templates.library.defi.apr_apy_calculator import (
    create_apr_apy_calculator_template,
)

# Trading Strategy Templates
from app.application.templates.library.trading.entry_exit_strategy import (
    create_entry_exit_strategy_template,
)
from app.application.templates.library.trading.stop_loss_optimization import (
    create_stop_loss_optimization_template,
)
from app.application.templates.library.trading.position_sizing import (
    create_position_sizing_template,
)
from app.application.templates.library.trading.dca_strategy_builder import (
    create_dca_strategy_builder_template,
)
from app.application.templates.library.trading.trend_analysis import (
    create_trend_analysis_template,
)

__all__ = [
    # Portfolio Management
    "create_portfolio_health_check_template",
    "create_risk_assessment_report_template",
    "create_yield_optimization_analysis_template",
    "create_rebalancing_recommendations_template",
    "create_tax_loss_harvesting_template",
    # DeFi Analysis
    "create_protocol_deep_dive_template",
    "create_risk_vs_reward_comparison_template",
    "create_smart_contract_security_analysis_template",
    "create_liquidity_analysis_template",
    "create_apr_apy_calculator_template",
    # Trading Strategies
    "create_entry_exit_strategy_template",
    "create_stop_loss_optimization_template",
    "create_position_sizing_template",
    "create_dca_strategy_builder_template",
    "create_trend_analysis_template",
]
