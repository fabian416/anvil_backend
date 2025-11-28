from app.infrastructure.agents.base import AnvilAgent
from app.infrastructure.agents.tools.hyperliquid import HyperliquidTools

class TradingAgent(AnvilAgent):
    def __init__(self):
        super().__init__(
            name="TradingAgent",
            model_id="gpt-4-turbo",
            tools=[HyperliquidTools()] # In real Agno, we wrap this
        )
