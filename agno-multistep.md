from agno import Agent, Team, Workflow
from agno.tools import Tool
import requests

# Tool: CoinGecko quote
class CoinGeckoTool(Tool):
    def execute(self, from_token: str, to_token: str, amount: float):
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_token.lower()},{to_token.lower()}&vs_currencies=usd"
        data = requests.get(url).json()
        rate = data[from_token.lower()]['usd'] / data[to_token.lower()]['usd']
        return f"1 {from_token} = {rate:.6f} {to_token}. Total: {amount * rate:.6f} {to_token}"

# Agent 1: Quote Finder
quote_agent = Agent(
    name="QuoteFinder",
    instructions="Analiza input y extrae from_token, to_token, amount. Devuelve formato claro.",
    tools=[CoinGeckoTool()]
)

# Agent 2: Confirmation
confirm_agent = Agent(
    name="SwapConfirmer",
    instructions="Recibe quote. Pregunta confirmación. Si OK, pasa a executor. Track amount.",
    memory=True
)

# Agent 3: Executor (Hyperliquid/1inch)
executor_agent = Agent(
    name="SwapExecutor",
    instructions="Ejecuta swap real via Hyperliquid/1inch con wallet API.",
    tools=[HyperliquidTool(), OneInchTool()]
)

# Workflow multistep
swap_team = Team(agents=[quote_agent, confirm_agent, executor_agent])

# Input usuario
user_input = "swap 0.1 ETH to BTC"

# Run workflow
result = swap_team.run(user_input)
print(result)

