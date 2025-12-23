# 03 - Asset Management

> **User Journey Stage**: The Holdings
> **Goal**: Manage, Transfer, and Track Ownership.

## 📖 Overview
This section covers the "Wallet" functionality. It is the accounting backbone of the user's experience. Accuracy and trust are paramount here.

## 🧩 Modules
1.  **Wallet (`FRONTEND_USER_WALLET_*.md`)**:
    - **Overview**: Token balances across chains.
    - **Send/Receive**: Core transfer logic with gas estimation.
    - **Token Details**: Historical performance of owned assets.
2.  **NFTs (`FRONTEND_USER_NFT_MARKETPLACE.md`)**:
    - Visual gallery of digital collectibles.
    - Floor price valuation.
3.  **Transactions (`FRONTEND_USER_TRANSACTIONS_HISTORY.md`)**:
    - Immutable ledger of user actions.

## 🎨 UX Guidelines
- **Precision**: Show up to 6 decimal places for tokens, but truncate visually with tooltips.
- **Safety**: "Double Confirm" modals for all outgoing transfers.
- **Clarity**: Using human-readable transaction statuses (e.g., "Minting..." vs "Pending").
