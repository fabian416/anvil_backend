"""
ULTRA Arbitrage tool definitions for chat integration.

These tool definitions allow the AI agent to invoke ULTRA Arbitrage capabilities
(flash loans, arbitrage discovery, MEV protection) during chat conversations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ULTRAToolType(Enum):
    """ULTRA Arbitrage tool types."""

    FLASH_LOANS = "ultra_flash_loans"
    ARBITRAGE_DISCOVERY = "ultra_arbitrage_discovery"
    MEV_PROTECTION = "ultra_mev_protection"
    AUTO_EXECUTOR = "ultra_auto_executor"


@dataclass(frozen=True)
class ULTRAToolDefinition:
    """
    ULTRA Arbitrage tool definition for agent use.

    Attributes:
        name: Tool function name
        type: ULTRA tool type
        description: Human-readable description of what the tool does
        parameters: Parameter schema (JSON Schema format)
    """

    name: str
    type: ULTRAToolType
    description: str
    parameters: Dict[str, Any]

    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to Agent Squad tool format.

        Returns:
            Dictionary in Agent Squad tool format
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# Predefined ULTRA Arbitrage tools available in chat
ULTRA_TOOLS: List[ULTRAToolDefinition] = [
    ULTRAToolDefinition(
        name="get_flash_loan_info",
        type=ULTRAToolType.FLASH_LOANS,
        description=(
            "Get information about flash loan protocols and best rates. "
            "Compares Aave V3, Balancer, and Uniswap V3 flash loan providers. "
            "Returns protocol details, fees, available liquidity, and recommendations. "
            "Use this to determine optimal flash loan source for arbitrage."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token to borrow via flash loan (e.g., ETH, USDC, DAI)",
                },
                "amount": {
                    "type": "number",
                    "description": "Amount to borrow (in token units, e.g., 100 for 100 ETH)",
                },
            },
            "required": ["token_symbol", "amount"],
        },
    ),
    ULTRAToolDefinition(
        name="discover_arbitrage",
        type=ULTRAToolType.ARBITRAGE_DISCOVERY,
        description=(
            "Scan for profitable arbitrage opportunities across DEXes. "
            "Analyzes 2-hop, 3-hop, and triangle arbitrage paths. "
            "Returns opportunities with profit estimates, gas costs, and execution paths. "
            "Filters by minimum profit threshold and sorts by profitability. "
            "Use this to find risk-free arbitrage opportunities."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Base token for arbitrage (e.g., ETH, USDC)",
                },
                "capital": {
                    "type": "number",
                    "description": "Available capital for arbitrage (in USD)",
                },
                "min_profit": {
                    "type": "number",
                    "description": "Minimum profit threshold in USD (default: 50)",
                    "default": 50,
                },
            },
            "required": ["token_symbol", "capital"],
        },
    ),
    ULTRAToolDefinition(
        name="check_mev_protection",
        type=ULTRAToolType.MEV_PROTECTION,
        description=(
            "Check MEV protection status and simulate protected execution. "
            "Uses Flashbots private relay to prevent front-running and sandwich attacks. "
            "Returns bundle simulation results, protection level, and execution strategy. "
            "Use this before executing high-value arbitrage to ensure MEV safety."
        ),
        parameters={
            "type": "object",
            "properties": {
                "opportunity_id": {
                    "type": "string",
                    "description": "Arbitrage opportunity ID from discovery (optional)",
                },
                "protection_level": {
                    "type": "string",
                    "description": "MEV protection level: standard, high, maximum (default: high)",
                    "default": "high",
                    "enum": ["standard", "high", "maximum"],
                },
            },
            "required": [],
        },
    ),
    ULTRAToolDefinition(
        name="get_auto_executor_status",
        type=ULTRAToolType.AUTO_EXECUTOR,
        description=(
            "Get automated arbitrage executor status and configuration. "
            "Shows current scanning status, executed trades, success rate, and total profit. "
            "Returns configuration settings, risk limits, and performance metrics. "
            "Use this to monitor automated arbitrage bot activity."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]


def get_ultra_tool_by_name(name: str) -> ULTRAToolDefinition | None:
    """
    Get ULTRA tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition if found, None otherwise
    """
    for tool in ULTRA_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_ultra_tool_by_type(tool_type: ULTRAToolType) -> ULTRAToolDefinition | None:
    """
    Get ULTRA tool definition by type.

    Args:
        tool_type: Tool type enum

    Returns:
        Tool definition if found, None otherwise
    """
    for tool in ULTRA_TOOLS:
        if tool.type == tool_type:
            return tool
    return None
