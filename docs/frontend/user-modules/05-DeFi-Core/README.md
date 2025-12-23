# 05 - DeFi Operations (Core)

> **User Journey Stage**: The Actions
> **Goal**: Execute standard financial strategies.

## 📖 Overview
These are the "Primitives" of DeFi. The documentation here defines the strict contracts for interacting with major external protocols (Curve, Aave, Axelar).

## 🧩 Modules
1.  **Swap (`FRONTEND_USER_DEFI_SWAP.md`)**:
    - Exchange assets (Curve/Uniswap).
2.  **Bridge (`FRONTEND_USER_DEFI_BRIDGE.md`)**:
    - Cross-chain transfers (Axelar).
3.  **Lending & Borrowing**:
    - **Supply** (`FRONTEND_USER_DEFI_SUPPLY.md`): Providing collateral.
    - **Borrow** (`FRONTEND_USER_DEFI_BORROW.md`): Taking loans against collateral.
4.  **Yield**:
    - **Earn** (`FRONTEND_USER_DEFI_EARN.md`): Aggregated yield farming.
    - **Stake** (`FRONTEND_USER_DEFI_STAKE.md`): Governance token staking.

## 🎨 UX Guidelines
- **Transparency**: Always show Fees, Slippage, and Estimated Time.
- **Feedback**: Real-time status updates for blockchain transactions (Pending -> Confirming -> Done).
- **Education**: Tooltips explaining "APY", "Health Factor", and "Impermanent Loss".
