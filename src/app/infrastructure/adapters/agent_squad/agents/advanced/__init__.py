"""
Agent Squad advanced agents.

Advanced Agents (4):
- BridgeCrosschainAgentAxelar: Layer 2 & cross-chain bridging
- LendingBorrowingAgentAave: Leverage & collateral optimization
- NFTAssetManagerAgentOpenSea: NFT portfolio management
- DAOGovernanceAgentSnapshot: DAO voting & governance

All implement AgentGateway interface.
"""

from .bridge_crosschain_agent_axelar import BridgeCrosschainAgentAxelar
from .lending_borrowing_agent_aave import LendingBorrowingAgentAave
from .nft_asset_manager_agent_opensea import NFTAssetManagerAgentOpenSea
from .dao_governance_agent_snapshot import DAOGovernanceAgentSnapshot

__all__ = [
    "BridgeCrosschainAgentAxelar",
    "LendingBorrowingAgentAave",
    "NFTAssetManagerAgentOpenSea",
    "DAOGovernanceAgentSnapshot",
]
