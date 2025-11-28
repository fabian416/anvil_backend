from typing import Dict, Any

class HyperliquidTools:
    """
    Tool definitions for Hyperliquid Interaction.
    """
    def get_positions(self, wallet_address: str) -> Dict[str, Any]:
        """
        Fetches open positions for a wallet on Hyperliquid.
        """
        # Mock implementation
        return {
            "positions": [
                {"coin": "ETH", "size": "1.5", "entryPx": "2000.00", "liquidationPx": "1800.00"}
            ]
        }

    def create_order_payload(self, coin: str, is_buy: bool, sz: float, limit_px: float) -> Dict[str, Any]:
        """
        Constructs an unsigned order payload for the frontend to sign.
        """
        return {
            "type": "order",
            "coin": coin,
            "is_buy": is_buy,
            "sz": sz,
            "limit_px": limit_px,
            "cloid": "123456789"
        }
