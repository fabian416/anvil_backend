"""DeFi Protocol Analysis Templates"""

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

__all__ = [
    "create_protocol_deep_dive_template",
    "create_risk_vs_reward_comparison_template",
    "create_smart_contract_security_analysis_template",
    "create_liquidity_analysis_template",
    "create_apr_apy_calculator_template",
]
