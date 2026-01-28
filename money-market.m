MoneyMarketHandler is your dedicated module (parallel to SwapHandler and LendingHandler) that abstracts Aave + Compound operations into unified Agno workflows for money market strategies.

Here are 8 production cases using MCP endpoints + Agno Team routing:

1. Smart Collateral Allocator
text
Input: {"wallet": "0x...", "deposit": 50000, "target_yield": 8%}
Agents: Scanner → Allocator → Executor
MCP: get_market_data(Aave), get_market_data(Compound)
Logic: Split USDC 70% Aave (higher yield) + 30% Compound (stability)
Output: PositionReport(aave_deposit=35000, comp_deposit=15000, blended_apy=8.2%)
2. Recursive Leverage Engine
text
Input: {"asset": "ETH", "target_ltv": 0.82, "max_health": 1.15}
Agents: Leverage → Risk → Rebalance
MCP: get_available_to_borrow, supply_asset(Aave), supply_asset(Compound)
Flow: Supply ETH → Borrow USDC → Swap → Supply USDC → Repeat
Output: LeverageReport(final_ltv=0.81, iterations=3, protocol_mix="80% Aave")
3. Yield Curve Optimizer
text
Input: {"horizon_days": 30, "risk_profile": "aggressive"}
Agents: Market → Forecaster → Positioner
MCP: get_market_data both protocols across assets
Logic: Short-term Aave (high util), long-term Compound (stable)
Output: YieldCurve(allocation=[{"asset": "USDC", "aave_pct": 60, "apy": 9.1}])
4. Liquidation Protection Vault
text
Input: {"min_health": 1.2, "wallet": "0x..."}
Agents: Monitor → AutoRepay → Rebalance
MCP: calculate_health_factor, repay_loan(Aave+Compound)
Flow: Health <1.2 → Repay from Compound cTokens → Rebalance to Aave
Output: ProtectionReport(repays_executed=2, avg_health=1.35)
5. Cross-Market Arbitrage
text
Input: {"base_asset": "USDC", "min_profit": 0.5}
Agents: RateScanner → ArbCalc → Executor
MCP: get_market_data(Aave vs Compound supply/borrow spreads)
Flow: Borrow cheap Compound USDC → Supply expensive Aave USDC
Output: ArbReport(net_profit=0.73%, txs=2, duration="2h")
6. Idle Cash Maximizer
text
Input: {"idle_eth": 2.5, "min_deposit": 0.1}
Agents: CashFlow → Deployer → Monitor
MCP: get_market_data, supply_asset (dynamic routing)
Logic: Deploy to highest APY market >$100 threshold
Output: Deployment(capital_deployed=2.3ETH, current_apy=7.8%)
7. Protocol Risk Balancer
text
Input: {"max_single_protocol": 60, "wallet": "0x..."}
Agents: Exposure → Rebalancer → Executor
MCP: get_user_positions(Aave+Compound)
Flow: >60% Aave → Withdraw 20% → Deposit Compound
Output: BalanceReport(aave_exposure=55%, comp_exposure=45%)
8. Emergency Deleverager
text
Input: {"emergency_wallet": "0x...", "safe_ltv": 0.5}
Agents: PanicTrigger → Unwinder → CashOut
MCP: get_liquidation_risk, withdraw_supply, repay_loan
Flow: Health <1.1 → Unwind ALL positions → Hold USDC
Output: Deleveraged(cash_remaining=48500 USDC, pnl=-2.1%)
MoneyMarket Team Implementation
python
money_market_team = Team(
    name="MoneyMarketHandler",
    members=[
        collateral_allocator, leverage_engine, 
        yield_optimizer, liquidation_protect,
        arb_scanner, idle_deployer, risk_balancer, 
        emergency_unwinder
    ],
    routing="action",  # "leverage", "protect", "arb", etc.
    input_schema=MoneyMarketInput,
    output_schema=MoneyMarketReport
)
Universal MoneyMarketInput
python
class MoneyMarketInput(BaseModel):
    wallet: str
    action: Literal["allocate", "leverage", "optimize", "protect", 
                   "arbitrage", "deploy", "balance", "emergency"]
    params: dict  # asset, amount, risk_profile, etc.
    protocols: list[str] = ["aave", "compound"]  # Auto-routing
MCP Abstraction Layer
python
# Single interface for both protocols
async def unified_get_rates(protocol: str, asset: str):
    if protocol == "aave":
        return await aave_mcp.get_market_data(asset)
    return await compound_mcp.get_market_data(asset)
Key Insight: MoneyMarketHandler creates a "CeFi-like" UX - users specify goals, handler routes across Aave/Compound optimally via MCP + Privy signing. Perfect for your sales automation platform
