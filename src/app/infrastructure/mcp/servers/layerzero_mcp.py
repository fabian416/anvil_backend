"""LayerZero MCP Server - Cross-Chain Messaging & OFT Transfers.

Exposes LayerZero protocol functionality as MCP tools for AI agents.
Provides message tracking, OFT transfers, chain discovery, and fee estimation.

Tools:
    - track_message: Track cross-chain message by transaction hash
    - get_message_history: Get message history for an address
    - get_chains: Get supported LayerZero chains
    - estimate_fees: Estimate cross-chain messaging fees
    - get_oft_transfers: Get OFT token transfers for an address
    - check_message_status: Check delivery status of a message

Integration Points:
    - LayerZero endpoints on all supported chains
    - LayerZero Scan API for message tracking
    - OFT token contracts
    - Fee oracle for gas estimation

Feature Flag: mcp.servers.layerzero_enabled
"""
from typing import Dict, Any, List, Optional

from app.infrastructure.mcp.base import MCPServer
from app.setup.config.mcp import MCPSettings, MCPServerDisabledError
from app.domain.ports.layerzero_gateway import LayerZeroGateway


class LayerZeroMCPServer(MCPServer):
    """
    MCP server for LayerZero cross-chain messaging.

    Provides AI agents with tools to:
    - Track cross-chain messages
    - Monitor OFT transfers
    - Discover supported chains
    - Estimate messaging fees
    - Check delivery status

    Example usage by agent:
        # Track a cross-chain message
        message = await call_tool("layerzero_track_message", {
            "tx_hash": "0x123...abc"
        })

        # Get message history
        history = await call_tool("layerzero_get_message_history", {
            "address": "0x...user",
            "limit": 20
        })

        # Estimate fees
        fees = await call_tool("layerzero_estimate_fees", {
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "payload_size": 200
        })
    """

    def __init__(
        self,
        layerzero_gateway: Optional[LayerZeroGateway] = None,
        settings: Optional[MCPSettings] = None,
    ):
        """
        Initialize LayerZero MCP server.

        Args:
            layerzero_gateway: LayerZero gateway for data access
            settings: MCP configuration settings

        Raises:
            MCPServerDisabledError: If LayerZero server is disabled
        """
        self.settings = settings or MCPSettings()

        # Check if server is enabled
        if not self.settings.enabled or not getattr(self.settings.servers, 'layerzero_enabled', False):
            raise MCPServerDisabledError(
                "LayerZero MCP server is disabled. "
                "Enable with mcp.servers.layerzero_enabled=true in config."
            )

        super().__init__(
            name="layerzero",
            version="1.0.0",
            description="LayerZero cross-chain messaging and OFT transfers",
        )

        self.layerzero_gateway = layerzero_gateway
        
        # Register tools
        self.setup_tools()

    def setup_tools(self):
        """Register LayerZero protocol tools."""

        # Tool 1: Track Message
        self.register_tool(
            name="layerzero_track_message",
            description=(
                "Track a cross-chain message by source transaction hash. "
                "Shows status, source/destination chains, and delivery info."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tx_hash": {
                        "type": "string",
                        "description": "Source chain transaction hash (0x...)",
                    },
                },
                "required": ["tx_hash"],
            },
            handler=self._track_message_handler,
        )

        # Tool 2: Get Message History
        self.register_tool(
            name="layerzero_get_message_history",
            description=(
                "Get cross-chain message history for an address. "
                "Shows sent and received messages across all chains."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet or contract address (0x...)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Maximum messages to return",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["sent", "received", "both"],
                        "default": "both",
                        "description": "Message direction filter",
                    },
                },
                "required": ["address"],
            },
            handler=self._get_message_history_handler,
        )

        # Tool 3: Get Chains
        self.register_tool(
            name="layerzero_get_chains",
            description=(
                "Get all LayerZero supported chains. "
                "Shows chain names, IDs, and endpoints."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "mainnet_only": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show only mainnet chains (filter testnets)",
                    },
                },
                "required": [],
            },
            handler=self._get_chains_handler,
        )

        # Tool 4: Estimate Fees
        self.register_tool(
            name="layerzero_estimate_fees",
            description=(
                "Estimate fees for sending a cross-chain message. "
                "Returns gas costs in both native token and USD."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "source_chain": {
                        "type": "string",
                        "description": "Source chain name (e.g., 'ethereum', 'arbitrum')",
                    },
                    "destination_chain": {
                        "type": "string",
                        "description": "Destination chain name",
                    },
                    "payload_size": {
                        "type": "integer",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 10000,
                        "description": "Payload size in bytes (default 100)",
                    },
                },
                "required": ["source_chain", "destination_chain"],
            },
            handler=self._estimate_fees_handler,
        )

        # Tool 5: Get OFT Transfers
        self.register_tool(
            name="layerzero_get_oft_transfers",
            description=(
                "Get OFT (Omnichain Fungible Token) transfers for an address. "
                "Shows cross-chain token transfers using LayerZero OFT standard."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet address (0x...)",
                    },
                    "token": {
                        "type": "string",
                        "description": "Filter by token symbol (optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Maximum transfers to return",
                    },
                },
                "required": ["address"],
            },
            handler=self._get_oft_transfers_handler,
        )

        # Tool 6: Check Message Status
        self.register_tool(
            name="layerzero_check_message_status",
            description=(
                "Check delivery status of a cross-chain message. "
                "Shows if message was delivered, failed, or is pending."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tx_hash": {
                        "type": "string",
                        "description": "Source transaction hash",
                    },
                },
                "required": ["tx_hash"],
            },
            handler=self._check_message_status_handler,
        )

    # =========================================================================
    # Tool Handlers
    # =========================================================================

    async def _track_message_handler(
        self,
        tx_hash: str,
    ) -> Dict[str, Any]:
        """Handler for track_message tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured"}

        try:
            message = await self.layerzero_gateway.track_message(tx_hash=tx_hash)

            if not message:
                return {
                    "error": "Message not found",
                    "tx_hash": tx_hash,
                    "suggestion": "Ensure transaction hash is from a LayerZero message",
                }

            return {
                "message_id": message.message_id,
                "status": message.status,
                "source_chain": message.source_chain,
                "destination_chain": message.destination_chain,
                "sender": message.sender,
                "receiver": message.receiver,
                "payload": message.payload[:100] + "..." if len(message.payload) > 100 else message.payload,
                "nonce": message.nonce,
                "source_tx": message.source_tx_hash,
                "destination_tx": message.destination_tx_hash if message.destination_tx_hash else "Pending",
                "timestamp": str(message.timestamp),
                "gas_used": str(message.gas_used) if message.gas_used else "N/A",
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_message_history_handler(
        self,
        address: str,
        limit: int = 50,
        direction: str = "both",
    ) -> Dict[str, Any]:
        """Handler for get_message_history tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured", "messages": []}

        try:
            messages = await self.layerzero_gateway.get_message_history(
                address=address,
                limit=limit,
            )

            # Filter by direction
            if direction == "sent":
                messages = [m for m in messages if m.sender.lower() == address.lower()]
            elif direction == "received":
                messages = [m for m in messages if m.receiver.lower() == address.lower()]

            message_data = []
            for m in messages:
                is_sender = m.sender.lower() == address.lower()
                msg_direction = "sent" if is_sender else "received"

                message_data.append({
                    "message_id": m.message_id,
                    "direction": msg_direction,
                    "status": m.status,
                    "source_chain": m.source_chain,
                    "destination_chain": m.destination_chain,
                    "counterparty": m.receiver if is_sender else m.sender,
                    "timestamp": str(m.timestamp),
                    "source_tx": m.source_tx_hash,
                })

            return {
                "messages": message_data,
                "count": len(message_data),
                "address": address,
            }

        except Exception as e:
            return {"error": str(e), "messages": []}

    async def _get_chains_handler(
        self,
        mainnet_only: bool = True,
    ) -> Dict[str, Any]:
        """Handler for get_chains tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured", "chains": []}

        try:
            chains = await self.layerzero_gateway.get_chains()

            # Filter testnets if mainnet_only
            if mainnet_only:
                chains = [c for c in chains if not c.is_testnet]

            chain_data = []
            for c in chains:
                chain_data.append({
                    "name": c.name,
                    "chain_id": c.chain_id,
                    "lz_chain_id": c.lz_chain_id,
                    "endpoint": c.endpoint_address,
                    "is_testnet": c.is_testnet,
                })

            return {
                "chains": chain_data,
                "count": len(chain_data),
                "mainnet_only": mainnet_only,
            }

        except Exception as e:
            return {"error": str(e), "chains": []}

    async def _estimate_fees_handler(
        self,
        source_chain: str,
        destination_chain: str,
        payload_size: int = 100,
    ) -> Dict[str, Any]:
        """Handler for estimate_fees tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured"}

        try:
            fees = await self.layerzero_gateway.estimate_fees(
                source_chain=source_chain,
                destination_chain=destination_chain,
                payload_size=payload_size,
            )

            return {
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "payload_size_bytes": payload_size,
                "native_fee": str(fees.native_fee),
                "native_fee_usd": f"${float(fees.native_fee_usd):,.2f}",
                "zro_fee": str(fees.zro_fee),
                "total_usd": f"${float(fees.total_fee_usd):,.2f}",
                "gas_limit": fees.gas_limit,
            }

        except Exception as e:
            return {"error": str(e)}

    async def _get_oft_transfers_handler(
        self,
        address: str,
        token: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Handler for get_oft_transfers tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured", "transfers": []}

        try:
            transfers = await self.layerzero_gateway.get_oft_transfers(
                address=address,
                limit=limit,
            )

            # Filter by token if specified
            if token:
                transfers = [t for t in transfers if token.upper() in t.token_symbol.upper()]

            transfer_data = []
            for t in transfers:
                is_sender = t.sender.lower() == address.lower()
                transfer_direction = "sent" if is_sender else "received"

                transfer_data.append({
                    "token": t.token_symbol,
                    "amount": str(t.amount),
                    "amount_usd": f"${float(t.amount_usd):,.2f}",
                    "direction": transfer_direction,
                    "source_chain": t.source_chain,
                    "destination_chain": t.destination_chain,
                    "counterparty": t.receiver if is_sender else t.sender,
                    "status": t.status,
                    "timestamp": str(t.timestamp),
                    "tx_hash": t.source_tx_hash,
                })

            return {
                "transfers": transfer_data,
                "count": len(transfer_data),
                "address": address,
            }

        except Exception as e:
            return {"error": str(e), "transfers": []}

    async def _check_message_status_handler(
        self,
        tx_hash: str,
    ) -> Dict[str, Any]:
        """Handler for check_message_status tool."""
        if not self.layerzero_gateway:
            return {"error": "LayerZero gateway not configured"}

        try:
            message = await self.layerzero_gateway.track_message(tx_hash=tx_hash)

            if not message:
                return {
                    "error": "Message not found",
                    "tx_hash": tx_hash,
                }

            status_details = {
                "delivered": "✅ Message successfully delivered on destination chain",
                "pending": "⏳ Message sent, waiting for delivery",
                "failed": "❌ Message delivery failed",
            }.get(message.status, "Unknown status")

            return {
                "tx_hash": tx_hash,
                "status": message.status,
                "status_details": status_details,
                "source_chain": message.source_chain,
                "destination_chain": message.destination_chain,
                "source_tx": message.source_tx_hash,
                "destination_tx": message.destination_tx_hash if message.destination_tx_hash else None,
                "timestamp": str(message.timestamp),
            }

        except Exception as e:
            return {"error": str(e)}


# Main entry point for running server standalone
if __name__ == "__main__":
    import uvicorn

    print("""
╔══════════════════════════════════════════════════════════╗
║        LayerZero MCP Server Starting...                 ║
╚══════════════════════════════════════════════════════════╝

Port: 8091

Tools Available:
  • track_message: Track cross-chain message by transaction hash
  • get_message_history: Get message history for an address
  • get_chains: Get supported LayerZero chains
  • estimate_fees: Estimate cross-chain messaging fees
  • get_oft_transfers: Get OFT token transfers for an address
  • check_message_status: Check delivery status of a message

Supported Chains:
  • 40+ EVM and non-EVM chains
  • Including Ethereum, Arbitrum, Optimism, Polygon, BSC, Avalanche, etc.

Endpoints:
  GET  /           - Server info
  GET  /tools      - List all tools
  POST /tools/{name} - Call a tool
  GET  /health     - Health check

Starting server...
    """)

    server = LayerZeroMCPServer()
    uvicorn.run(server.app, host="0.0.0.0", port=8091, log_level="info")
