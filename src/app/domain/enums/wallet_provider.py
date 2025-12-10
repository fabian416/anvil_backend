from enum import Enum


class WalletProvider(Enum):
    """Types of wallet providers/origins."""
    
    PRIVY = "privy"
    """Privy embedded wallet created by the SDK."""
    
    EXTERNAL = "external"
    """External wallet connected via browser extension (MetaMask, etc.)."""
    
    IMPORTED = "imported"
    """Wallet imported via private key through Privy's import flow."""
