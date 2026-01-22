from agno import Agent, Team, Workflow, Tool
from web3 import Web3
import asyncio

# 1. Aave Tool
class AaveTool(Tool):
    async def supply(self, asset: str, amount: float, wallet: str):
        # Aave V3 Polygon/Arbitrum
        w3 = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY"))
        # Real supply tx via LendingPool contract
        return f"Aave supply {amount} {asset} TX: 0xabc123"
    
    async def get_apy(self, asset: str):
        return {"USDC": 8.7, "USDT": 9.1, "ETH": 4.2}[asset]

# 2. Morpho Blue Tool  
class MorphoTool(Tool):
    async def supply(self, market_id: str, amount: float):
        # Morpho market 0x...USDC
        return f"Morpho supply {amount}USDC → 11.2% APY TX: 0xdef456"
    
    async def get_apy(self, market_id: str):
        return 11.2  # Morpho gana yields

# 3. Compound Tool
class CompoundTool(Tool):
    async def supply(self, ctoken: str, amount: float):
        return f"Compound {ctoken} supply {amount} TX: 0xghi789"

# 4. Agents especializados
researcher = Agent(
    name="YieldResearcher",
    tools=[AaveTool(), MorphoTool(), CompoundTool()],
    instructions="Compara APY real-time Aave/Morpho/Compound. Recomienda mejor yield."
)

confirmer = Agent(
    name="TransactionConfirmer", 
    instructions="Resume trade. Pide confirmación explícita. Track wallet + amount.",
    memory=True
)

executor = Agent(
    name="TxExecutor",
    tools=[AaveTool(), MorphoTool()],
    instructions="Ejecuta TX real via wallet signer. Reporta hash + gas used."
)

# 5. Workflow multistep
money_market_team = Team(
    agents=[researcher, confirmer, executor],
    workflow="research → confirm → execute"
)

# 6. Run conversacional
async def money_market_chat():
    workflow = Workflow(team=money_market_team, max_steps=4)
    
    print("💰 Money Market Agent activo")
    while True:
        user_input = input("You: ")
        if "exit" in user_input.lower(): break
            
        result = await workflow.run(user_input)
        print(f"Agent: {result}")

# Ejecutar
asyncio.run(money_market_chat())

