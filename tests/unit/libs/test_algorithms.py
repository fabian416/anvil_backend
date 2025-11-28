import sys
import os
import pytest

# Add the library path to sys.path
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../libs/competitive-programmer-handbook-python/src"))
sys.path.append(lib_path)

from algorithms.graph import Graph, dijkstra, bellman_ford, edmonds_karp
from algorithms.dp import knapsack_01, Item

def test_dijkstra():
    g = Graph[str]()
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "C", 2.0)
    g.add_edge("A", "C", 10.0)
    
    distances, predecessors = dijkstra(g, "A")
    
    assert distances["A"] == 0.0
    assert distances["B"] == 1.0
    assert distances["C"] == 3.0 # A->B->C is 1+2=3, better than 10
    assert predecessors["C"] == "B"

def test_bellman_ford_negative_cycle():
    g = Graph[str]()
    # A -> B -> C -> A with net negative weight
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "C", -5.0)
    g.add_edge("C", "A", 2.0)
    
    _, _, has_cycle = bellman_ford(g, "A")
    assert has_cycle is True

def test_edmonds_karp():
    g = Graph[str]()
    # S -> A (10), S -> B (10)
    # A -> B (2), A -> T (4), A -> C (8)
    # B -> T (9), B -> D (10)
    # D -> T (10)
    # C -> T (10)
    
    # Simple case: S -> A -> T (cap 10)
    g.add_edge("S", "A", 10.0)
    g.add_edge("A", "T", 10.0)
    
    max_flow = edmonds_karp(g, "S", "T")
    assert max_flow == 10.0
    
    # Diamond: S->A(3), S->B(2), A->T(3), B->T(2)
    g2 = Graph[str]()
    g2.add_edge("S", "A", 3.0)
    g2.add_edge("S", "B", 2.0)
    g2.add_edge("A", "T", 3.0)
    g2.add_edge("B", "T", 2.0)
    
    assert edmonds_karp(g2, "S", "T") == 5.0

def test_knapsack():
    items = [
        Item(weight=10, value=60),
        Item(weight=20, value=100),
        Item(weight=30, value=120),
    ]
    capacity = 50
    
    max_val, selected = knapsack_01(items, capacity)
    # Optimal: 20 (100) + 30 (120) = 220
    assert max_val == 220.0
