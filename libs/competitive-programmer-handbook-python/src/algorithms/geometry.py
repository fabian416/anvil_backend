from typing import List, Tuple, NamedTuple
import math

class Point(NamedTuple):
    x: float
    y: float

def cross_product(o: Point, a: Point, b: Point) -> float:
    """
    Returns the cross product of vectors OA and OB.
    A positive cross product indicates a counter-clockwise turn,
    negative indicates clockwise, and 0 indicates collinear.
    (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
    """
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

def convex_hull(points: List[Point]) -> List[Point]:
    """
    Computes the convex hull of a set of 2D points using the Monotone Chain algorithm.
    
    Args:
        points: List of Points (x, y).
        
    Returns:
        List of Points on the convex hull in counter-clockwise order.
    """
    n = len(points)
    if n <= 2:
        return points

    # Sort points lexicographically (by x, then by y)
    sorted_points = sorted(points, key=lambda p: (p.x, p.y))

    # Build lower hull
    lower = []
    for p in sorted_points:
        while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(sorted_points):
        while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenate lower and upper hulls
    # The last point of each list is the first point of the other list, so we remove duplicates
    return lower[:-1] + upper[:-1]
