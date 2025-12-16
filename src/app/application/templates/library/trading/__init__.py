"""Trading Strategy Templates"""

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
    "create_entry_exit_strategy_template",
    "create_stop_loss_optimization_template",
    "create_position_sizing_template",
    "create_dca_strategy_builder_template",
    "create_trend_analysis_template",
]
