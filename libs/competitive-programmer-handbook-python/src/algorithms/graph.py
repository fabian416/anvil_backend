import heapq
import math
from typing import Dict, List, Optional, Tuple, TypeVar, Generic

T = TypeVar("T")

class Graph(Generic[T]):
    """
    A generic graph representation using an adjacency list.
    Nodes can be of any hashable type T (e.g., str, int, UUID).
    """
    def __init__(self):
        self.adj: Dict[T, Dict[T, float]] = {}

    def add_edge(self, u: T, v: T, weight: float, directed: bool = True):
        if u not in self.adj:
            self.adj[u] = {}
        if v not in self.adj:
            self.adj[v] = {}
        
        self.adj[u][v] = weight
        if not directed:
            self.adj[v][u] = weight

    def get_nodes(self) -> List[T]:
        return list(self.adj.keys())

    def get_neighbors(self, u: T) -> Dict[T, float]:
        return self.adj.get(u, {})


def dijkstra(graph: Graph[T], start_node: T, end_node: Optional[T] = None) -> Tuple[Dict[T, float], Dict[T, Optional[T]]]:
    """
    Implements Dijkstra's algorithm for finding shortest paths from a start node.
    
    Args:
        graph: The Graph instance.
        start_node: The starting node.
        end_node: Optional target node to stop early if found.
        
    Returns:
        Tuple containing:
        - distances: Dict mapping nodes to their shortest distance from start.
        - predecessors: Dict mapping nodes to their predecessor in the shortest path.
    """
    distances: Dict[T, float] = {node: float('inf') for node in graph.get_nodes()}
    distances[start_node] = 0.0
    predecessors: Dict[T, Optional[T]] = {node: None for node in graph.get_nodes()}
    
    # Priority queue stores tuples of (distance, node)
    pq: List[Tuple[float, T]] = [(0.0, start_node)]
    
    visited = set()

    while pq:
        current_dist, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        if end_node and u == end_node:
            break

        if current_dist > distances[u]:
            continue

        for v, weight in graph.get_neighbors(u).items():
            if v in visited:
                continue
                
            new_dist = current_dist + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    return distances, predecessors


def reconstruct_path(predecessors: Dict[T, Optional[T]], end_node: T) -> List[T]:
    """
    Reconstructs the path from start to end using the predecessor map.
    """
    path = []
    current = end_node
    while current is not None:
        path.append(current)
        current = predecessors.get(current)
    return path[::-1]


def bellman_ford(graph: Graph[T], start_node: T) -> Tuple[Dict[T, float], Dict[T, Optional[T]], bool]:
    """
    Implements Bellman-Ford algorithm to find shortest paths and detect negative cycles.
    
    Returns:
        Tuple containing:
        - distances
        - predecessors
        - has_negative_cycle (bool)
    """
    nodes = graph.get_nodes()
    distances: Dict[T, float] = {node: float('inf') for node in nodes}
    distances[start_node] = 0.0
    predecessors: Dict[T, Optional[T]] = {node: None for node in nodes}

    # Relax edges |V| - 1 times
    for _ in range(len(nodes) - 1):
        changed = False
        for u in nodes:
            if distances[u] == float('inf'):
                continue
            for v, weight in graph.get_neighbors(u).items():
                if distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    predecessors[v] = u
                    changed = True
        if not changed:
            break

    # Check for negative cycles
    has_negative_cycle = False
    for u in nodes:
        if distances[u] == float('inf'):
            continue
        for v, weight in graph.get_neighbors(u).items():
            if distances[u] + weight < distances[v]:
                has_negative_cycle = True
                break
        if has_negative_cycle:
            break

    return distances, predecessors, has_negative_cycle


def edmonds_karp(graph: Graph[T], source: T, sink: T) -> float:
    """
    Implements Edmonds-Karp algorithm for Maximum Flow.
    Note: This requires a residual graph setup which is slightly different from the standard Graph class.
    We will build a local residual graph structure for this calculation.
    """
    # Build residual graph with capacities
    capacity: Dict[T, Dict[T, float]] = {}
    graph_nodes = graph.get_nodes()
    
    # Initialize capacity dict for all nodes first
    for u in graph_nodes:
        capacity[u] = {}
        
    # Fill capacities from graph edges
    for u in graph_nodes:
        for v, weight in graph.get_neighbors(u).items():
            capacity[u][v] = weight
            # Ensure reverse edge exists in capacity map
            if v not in capacity:
                capacity[v] = {}
            if u not in capacity[v]:
                capacity[v][u] = 0.0

    max_flow = 0.0

    while True:
        # BFS to find augmenting path
        parent: Dict[T, Optional[T]] = {node: None for node in graph_nodes}
        queue = [(source, float('inf'))]
        parent[source] = source # Mark source as visited
        
        path_flow = 0.0
        path_end = None

        while queue:
            u, flow = queue.pop(0)
            if u == sink:
                path_flow = flow
                path_end = sink
                break
            
            if u not in capacity: continue

            for v, cap in capacity[u].items():
                if parent.get(v) is None and cap > 0:
                    parent[v] = u
                    new_flow = min(flow, cap)
                    queue.append((v, new_flow))
            
            if path_end: break
        
        if not path_end:
            break # No augmenting path found

        max_flow += path_flow
        curr = sink
        while curr != source:
            prev = parent[curr]
            if prev is None: # Should not happen if path found
                break
            capacity[prev][curr] -= path_flow
            capacity[curr][prev] += path_flow
            curr = prev

    return max_flow
