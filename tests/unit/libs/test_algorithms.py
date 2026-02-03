import sys
import os
import pytest

# Add the library path to sys.path
lib_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../libs/competitive-programmer-handbook-python/src",
    )
)
sys.path.append(lib_path)

from algorithms.graph import Graph, dijkstra, bellman_ford, edmonds_karp
from algorithms.dp import knapsack_01, Item
from algorithms.geometry import Point, convex_hull
from algorithms.range_queries import SumSegmentTree, MinSegmentTree


def test_dijkstra():
    g = Graph[str]()
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "C", 2.0)
    g.add_edge("A", "C", 10.0)

    distances, predecessors = dijkstra(g, "A")

    assert distances["A"] == 0.0
    assert distances["B"] == 1.0
    assert distances["C"] == 3.0  # A->B->C is 1+2=3, better than 10
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


def test_convex_hull():
    points = [
        Point(0, 0),
        Point(1, 1),
        Point(2, 2),  # Interior (collinear)
        Point(0, 2),
        Point(2, 0),
        Point(1, 0.5),  # Interior
    ]

    hull = convex_hull(points)

    # Expected hull: (0,0) -> (2,0) -> (2,2) -> (0,2) (order may vary in start point, but must be CCW)

    assert len(hull) == 4

    # Check presence
    hull_set = set(hull)
    assert Point(0, 0) in hull_set
    assert Point(2, 0) in hull_set
    assert Point(0, 2) in hull_set
    assert (
        Point(2, 2) in hull_set
    )  # Actually, (2,2) is extreme point, so it should be in hull.

    # (1, 0.5) is strictly inside, should not be in hull
    assert Point(1, 0.5) not in hull_set


def test_segment_tree_sum():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    st = SumSegmentTree(data)

    # Query range [2, 5) -> sum(3, 4, 5) = 12
    assert st.query(2, 5) == 12

    # Update index 2 (value 3) to 10
    st.update(2, 10)
    # New data: 1, 2, 10, 4, 5, 6, 7, 8

    # Query range [2, 5) -> sum(10, 4, 5) = 19
    assert st.query(2, 5) == 19


def test_segment_tree_min():
    data = [5.0, 2.0, 9.0, 1.0, 7.0]
    st = MinSegmentTree(data)

    # Range [0, 5) -> min is 1.0
    assert st.query(0, 5) == 1.0

    # Range [0, 3) -> min(5, 2, 9) -> 2.0
    assert st.query(0, 3) == 2.0

    # Update index 3 (value 1.0) to 10.0
    st.update(3, 10.0)
    # Data: 5, 2, 9, 10, 7

    # Range [0, 5) -> min is 2.0
    assert st.query(0, 5) == 2.0
