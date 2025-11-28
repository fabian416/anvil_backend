# Competitive Programmer Handbook Algorithm Specifications

## 1. Strategic Note
Since the library repository is currently sparse, we will implement these algorithms from scratch using the handbook as a reference guide.

## 2. Graph Algorithms (Module: `13-Shortest Paths`)

### Dijkstra's Algorithm (Optimized)
- **Purpose**: Finding the best swap route across multiple DEX pools.
- **Input**: 
    - `graph`: Adjacency list where `node` = Token, `edge_weight` = -log(price) (to turn product of prices into sum of logs for shortest path).
    - `start_node`: Token In.
    - `end_node`: Token Out.
- **Output**: List of pools to route through.
- **Complexity**: `O(E + V log V)` using a priority queue.

### Bellman-Ford Algorithm
- **Purpose**: Detecting arbitrage opportunities (negative cycles in the log-price graph).
- **Input**: Graph of token pairs.
- **Output**: Cycle path if found (Profit loop).
- **Complexity**: `O(V * E)`. Slower, run only periodically via Celery.

## 3. Network Flow (Module: `20-Flows And Cuts`)

### Edmonds-Karp Algorithm
- **Purpose**: Calculating maximum liquidity flow between two tokens (how much can I swap before slippage becomes infinite?).
- **Input**: Graph where capacity = pool depth.
- **Output**: Max flow value.
- **Complexity**: `O(V * E^2)`.

## 4. Dynamic Programming (Module: `07-Dynamic Programming`)

### Knapsack Problem (0/1 and Unbounded)
- **Purpose**: Portfolio construction. Given capital `C`, select assets `A_i` with expected return `R_i` and risk `W_i` such that total risk < MaxRisk.
- **Input**: List of Opportunities (Yield Farms).
- **Output**: Optimal set of investments.
- **Complexity**: `O(N * W)`.

## 5. Implementation Plan
1.  Create `src/algorithms/graph.py` and `src/algorithms/dp.py` within the library.
2.  Implement Dijkstra first (Highest Priority for MVP).
3.  Add Unit Tests verifying correctness against known cases.
