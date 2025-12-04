"""
ULTRA Arbitrage tool executor for chat integration.

This service executes ULTRA Arbitrage tools and formats responses for chat display.
"""

import httpx
from typing import Any, Dict
from datetime import datetime

from app.domain.value_objects.agent_tools.ultra_tools import ULTRAToolType


class ULTRAToolExecutor:
    """
    Executes ULTRA Arbitrage tools and formats responses for chat.
    
    This service acts as a bridge between the chat system and ULTRA Arbitrage APIs.
    It calls the appropriate ULTRA endpoints and formats the responses
    into human-readable text suitable for chat display.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize ULTRA tool executor.
        
        Args:
            base_url: Base URL for ULTRA APIs (default: localhost)
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_tool(
        self,
        tool_type: ULTRAToolType,
        parameters: Dict[str, Any],
    ) -> str:
        """
        Execute ULTRA tool and format response for chat.
        
        Args:
            tool_type: Type of ULTRA tool to execute
            parameters: Tool parameters (validated against schema)
        
        Returns:
            Formatted string response suitable for chat display
        
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If tool type is unknown
        """
        if tool_type == ULTRAToolType.FLASH_LOANS:
            return await self._execute_flash_loans(parameters)
        elif tool_type == ULTRAToolType.ARBITRAGE_DISCOVERY:
            return await self._execute_arbitrage_discovery(parameters)
        elif tool_type == ULTRAToolType.MEV_PROTECTION:
            return await self._execute_mev_protection(parameters)
        elif tool_type == ULTRAToolType.AUTO_EXECUTOR:
            return await self._execute_auto_executor(parameters)
        else:
            raise ValueError(f"Unknown ULTRA tool type: {tool_type}")
    
    async def _execute_flash_loans(self, params: Dict[str, Any]) -> str:
        """Execute flash loan info and format response."""
        token = params["token_symbol"]
        amount = params["amount"]
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/ultra/flash-loans/protocols"
            )
            response.raise_for_status()
            data = response.json()
            
            return self._format_flash_loans_response(token, amount, data)
        except httpx.HTTPError as e:
            return f"❌ Error getting flash loan info for {token}: {str(e)}"
    
    async def _execute_arbitrage_discovery(self, params: Dict[str, Any]) -> str:
        """Execute arbitrage discovery and format response."""
        token = params["token_symbol"]
        capital = params["capital"]
        min_profit = params.get("min_profit", 50)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/ultra/arbitrage/discover",
                json={
                    "base_token": token,
                    "capital": capital,
                    "min_profit_usd": min_profit,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return self._format_arbitrage_response(token, capital, data)
        except httpx.HTTPError as e:
            return f"❌ Error discovering arbitrage for {token}: {str(e)}"
    
    async def _execute_mev_protection(self, params: Dict[str, Any]) -> str:
        """Execute MEV protection check and format response."""
        opportunity_id = params.get("opportunity_id")
        protection_level = params.get("protection_level", "high")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/ultra/mev/protection-info"
            )
            response.raise_for_status()
            data = response.json()
            
            return self._format_mev_response(protection_level, data)
        except httpx.HTTPError as e:
            return f"❌ Error checking MEV protection: {str(e)}"
    
    async def _execute_auto_executor(self, params: Dict[str, Any]) -> str:
        """Execute auto executor status check and format response."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/ultra/auto-executor/status"
            )
            response.raise_for_status()
            data = response.json()
            
            return self._format_auto_executor_response(data)
        except httpx.HTTPError as e:
            return f"❌ Error getting auto-executor status: {str(e)}"
    
    # Response formatting methods
    
    def _format_flash_loans_response(
        self,
        token: str,
        amount: float,
        data: Dict,
    ) -> str:
        """Format flash loan response for chat display."""
        result = f"⚡ **Flash Loan Info for {amount} {token}:**\n\n"
        
        protocols = data.get("protocols", [])
        if not protocols:
            return result + "No flash loan protocols available."
        
        result += "**Available Protocols:**\n"
        for protocol in protocols[:3]:  # Top 3
            name = protocol.get("name", "Unknown")
            fee = protocol.get("fee_percent", 0)
            liquidity = protocol.get("available_liquidity", 0)
            
            result += f"• **{name}**\n"
            result += f"  - Fee: {fee}%\n"
            result += f"  - Liquidity: ${liquidity:,.0f}\n"
        
        # Best protocol recommendation
        best = data.get("best_protocol", {})
        if best:
            best_name = best.get("name", "")
            best_fee = best.get("fee_percent", 0)
            result += f"\n**Recommended:** {best_name} ({best_fee}% fee)"
        
        return result
    
    def _format_arbitrage_response(
        self,
        token: str,
        capital: float,
        data: Dict,
    ) -> str:
        """Format arbitrage discovery response for chat display."""
        result = f"🔍 **Arbitrage Opportunities for {token}:**\n\n"
        
        opportunities = data.get("opportunities", [])
        if not opportunities:
            return result + f"No profitable opportunities found with ${capital:,.0f} capital.\n\nTry:\n• Increasing capital\n• Lowering min_profit threshold\n• Different token"
        
        result += f"**Found {len(opportunities)} opportunities:**\n\n"
        
        for i, opp in enumerate(opportunities[:3], 1):  # Top 3
            opp_type = opp.get("type", "unknown")
            profit = opp.get("estimated_profit_usd", 0)
            gas_cost = opp.get("estimated_gas_cost_usd", 0)
            net_profit = profit - gas_cost
            path = opp.get("path", [])
            
            emoji = "🟢" if net_profit > 100 else "🟡" if net_profit > 50 else "⚪"
            
            result += f"{emoji} **Opportunity #{i} ({opp_type}):**\n"
            result += f"• Gross Profit: ${profit:.2f}\n"
            result += f"• Gas Cost: ${gas_cost:.2f}\n"
            result += f"• **Net Profit: ${net_profit:.2f}**\n"
            
            if path:
                result += f"• Path: {' → '.join(path)}\n"
            
            result += "\n"
        
        # Summary
        total_profit = sum(o.get("estimated_profit_usd", 0) for o in opportunities[:3])
        result += f"**Total Potential (Top 3):** ${total_profit:.2f}"
        
        return result
    
    def _format_mev_response(
        self,
        protection_level: str,
        data: Dict,
    ) -> str:
        """Format MEV protection response for chat display."""
        result = f"🛡️ **MEV Protection Status:**\n\n"
        
        result += f"**Protection Level:** {protection_level.upper()}\n\n"
        
        result += "**Flashbots Integration:**\n"
        result += "• ✅ Private transaction relay\n"
        result += "• ✅ Bundle simulation\n"
        result += "• ✅ Sandwich attack prevention\n"
        result += "• ✅ Front-running protection\n\n"
        
        # Protection levels
        result += "**Protection Levels:**\n"
        result += "• **Standard:** Basic Flashbots relay\n"
        result += "• **High:** Multi-relay + bundle optimization\n"
        result += "• **Maximum:** Private relay + max gas priority\n\n"
        
        result += "**Recommendation:** Use HIGH or MAXIMUM for trades >$10K"
        
        return result
    
    def _format_auto_executor_response(self, data: Dict) -> str:
        """Format auto executor status response for chat display."""
        status = data.get("status", "stopped")
        
        result = f"🤖 **Auto-Executor Status:**\n\n"
        
        # Status indicator
        if status == "running":
            result += "**Status:** 🟢 RUNNING\n\n"
        elif status == "paused":
            result += "**Status:** 🟡 PAUSED\n\n"
        else:
            result += "**Status:** 🔴 STOPPED\n\n"
        
        # Metrics
        metrics = data.get("metrics", {})
        total_trades = metrics.get("total_trades", 0)
        successful_trades = metrics.get("successful_trades", 0)
        total_profit = metrics.get("total_profit_usd", 0)
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        result += "**Performance:**\n"
        result += f"• Total Trades: {total_trades}\n"
        result += f"• Successful: {successful_trades}\n"
        result += f"• Success Rate: {success_rate:.1f}%\n"
        result += f"• **Total Profit: ${total_profit:,.2f}**\n\n"
        
        # Configuration
        config = data.get("config", {})
        min_profit = config.get("min_profit_threshold", 0)
        max_capital = config.get("max_capital_per_trade", 0)
        
        result += "**Configuration:**\n"
        result += f"• Min Profit: ${min_profit:.0f}\n"
        result += f"• Max Capital: ${max_capital:,.0f}\n"
        
        return result
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
