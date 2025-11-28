# Recommenders Library Specification

## 1. Strategic Overview (CTO Perspective)
**Recommenders** transforms our platform from a "Passive Tool" (User asks -> We answer) into an "Active Advisor" (We suggest -> User accepts).

We will use this library to build a **DeFi Recommendation Engine** that learns from on-chain behavior and user interactions. It moves us beyond generic "Top 10 Pools" lists to personalized "Alpha".

## 2. Use Cases

### Primary: Yield Farm Personalization
-   **Scenario**: "Show me farming opportunities."
-   **Execution**:
    -   *Collaborative Filtering*: "Users with similar wallet compositions to you also deposited in Convex."
    -   *Content-Based*: "You hold stablecoins and dislike impermanent loss; here is a single-sided USDC vault."

### Secondary: Agent Discovery
-   **Scenario**: User logs in.
-   **Execution**: "Based on market volatility, we recommend speaking to the **Risk Agent** today."

## 3. Architecture & Integration

### System Fit
Recommenders acts as a **Domain Service** (`RecommendationEngine`) consumed by the `PortfolioAgent`.

### Key Algorithms
-   **SAR (Smart Adaptive Recommendations)**: Fast, scalable algorithm for implicit feedback (clicks, trades).
-   **NCF (Neural Collaborative Filtering)**: Deep learning approach for complex user-item interactions.

## 4. Implementation Strategy
1.  **Data Engineering**: Build a "User-Item Matrix".
    -   *Users*: Wallet Addresses.
    -   *Items*: DeFi Protocols/Pools.
    -   *Interaction*: Tx Count / Volume.
2.  **Training**: Periodically retrain models on the `transactions` table.
3.  **Inference**: Real-time scoring via the API.

## 5. Roadmap
-   [ ] **Phase 1**: Build the User-Protocol Interaction Matrix from historical data.
-   [ ] **Phase 2**: Train a SAR model (CPU-friendly).
-   [ ] **Phase 3**: Expose `get_recommendations(user_id)` via the Portfolio Agent.
