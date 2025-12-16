"""
Conversation Template Library

Pre-built conversation templates for common DeFi and portfolio management workflows.

Categories:
- Portfolio Management: Health checks, risk assessment, rebalancing, tax optimization
- DeFi Analysis: Protocol analysis, yield optimization, liquidity analysis
- Trading Strategies: Entry/exit strategies, position sizing, DCA builders
"""

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
from app.application.templates.library.defi.protocol_deep_dive import (
    create_protocol_deep_dive_template,
)

__all__ = [
    "create_portfolio_health_check_template",
    "create_risk_assessment_report_template",
    "create_yield_optimization_analysis_template",
    "create_rebalancing_recommendations_template",
    "create_tax_loss_harvesting_template",
    "create_protocol_deep_dive_template",
]
