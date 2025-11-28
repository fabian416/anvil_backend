from typing import List, Callable, TypeVar, Generic, Optional

T = TypeVar("T")

class SegmentTree(Generic[T]):
    """
    A Generic Segment Tree implementation for range queries and point updates.
    Supports arbitrary associative operations (sum, min, max, gcd, etc.).
    """
    def __init__(self, data: List[T], operation: Callable[[T, T], T], identity_element: T):
        """
        Args:
            data: Initial list of values.
            operation: Binary associative function (e.g., lambda x, y: x + y).
            identity_element: Identity element for the operation (e.g., 0 for sum, float('inf') for min).
        """
        self.n = len(data)
        self.op = operation
        self.id = identity_element
        self.tree = [self.id] * (2 * self.n)
        
        # Build the tree
        for i in range(self.n):
            self.tree[self.n + i] = data[i]
            
        for i in range(self.n - 1, 0, -1):
            self.tree[i] = self.op(self.tree[2 * i], self.tree[2 * i + 1])

    def update(self, index: int, value: T):
        """
        Updates the value at `index` to `value`.
        Complexity: O(log n)
        """
        pos = index + self.n
        self.tree[pos] = value
        
        while pos > 1:
            self.tree[pos >> 1] = self.op(self.tree[pos], self.tree[pos ^ 1])
            pos >>= 1

    def query(self, left: int, right: int) -> T:
        """
        Queries the range [left, right) (inclusive left, exclusive right).
        Complexity: O(log n)
        """
        res_l = self.id
        res_r = self.id
        
        l = left + self.n
        r = right + self.n
        
        while l < r:
            if l & 1:
                res_l = self.op(res_l, self.tree[l])
                l += 1
            if r & 1:
                r -= 1
                res_r = self.op(self.tree[r], res_r)
            l >>= 1
            r >>= 1
            
        return self.op(res_l, res_r)

# Convenience Helpers
class SumSegmentTree(SegmentTree[int]):
    def __init__(self, data: List[int]):
        super().__init__(data, lambda a, b: a + b, 0)

class MinSegmentTree(SegmentTree[float]):
    def __init__(self, data: List[float]):
        super().__init__(data, min, float('inf'))
