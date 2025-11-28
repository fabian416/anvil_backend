from typing import List, Tuple, NamedTuple

class Item(NamedTuple):
    weight: int
    value: float
    name: str = ""

def knapsack_01(items: List[Item], capacity: int) -> Tuple[float, List[Item]]:
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming.
    Each item can be picked at most once.
    
    Args:
        items: List of Items (weight, value).
        capacity: Maximum weight capacity.
        
    Returns:
        Tuple of (max_value, list_of_selected_items)
    """
    n = len(items)
    # dp[i][w] = max value using first i items with capacity w
    dp = [[0.0 for _ in range(capacity + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        item = items[i-1]
        for w in range(capacity + 1):
            if item.weight <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w - item.weight] + item.value)
            else:
                dp[i][w] = dp[i-1][w]

    # Backtrack to find selected items
    selected_items = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            item = items[i-1]
            selected_items.append(item)
            w -= item.weight

    return dp[n][capacity], selected_items

def knapsack_unbounded(items: List[Item], capacity: int) -> float:
    """
    Solves the Unbounded Knapsack problem (items can be picked multiple times).
    Optimized 1D DP array.
    
    Args:
        items: List of Items.
        capacity: Maximum weight.
        
    Returns:
        max_value
    """
    # dp[w] = max value with capacity w
    dp = [0.0] * (capacity + 1)

    for w in range(capacity + 1):
        for item in items:
            if item.weight <= w:
                dp[w] = max(dp[w], dp[w - item.weight] + item.value)

    return dp[capacity]
