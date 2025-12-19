"""Portfolio domain entities."""

from app.domain.portfolio.entities.user_portfolio import UserPortfolio, ProtocolExposure

# Try to import portfolio_snapshot if it exists
try:
    from app.domain.portfolio.entities.portfolio_snapshot import PortfolioSnapshot
    __all__ = ["UserPortfolio", "ProtocolExposure", "PortfolioSnapshot"]
except ImportError:
    __all__ = ["UserPortfolio", "ProtocolExposure"]

