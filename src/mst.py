"""Minimum spanning trees: Prim (heapq) and Kruskal (union-find)."""
from src.graph import MinHeap


class UnionFind:
    """Disjoint sets with path compression + union by rank. Amortized ~O(alpha(n)) per op."""

    def __init__(self, items):
        # Time: O(n)
        self.parent = {x: x for x in items}
        self.rank = {x: 0 for x in items}

    def find(self, x):
        # Time: amortized O(alpha(n)) ~ O(1)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        """Returns False if already joined. Time: amortized O(alpha(n))."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def prim(g, start=None):
    """Prim's MST with binary heap. Returns (edges, total_weight).
    Time: O(E log V). Space: O(V + E)."""
    if not g.adj:
        return [], 0.0
    start = start or next(iter(g.adj))
    seen = {start}
    heap = MinHeap()
    for v, w in g.adj[start]:
        heap.push(w, (start, v))
    mst, total = [], 0.0
    while len(heap) and len(seen) < g.num_vertices():
        w, (u, v) = heap.pop()
        if v in seen:
            continue
        seen.add(v)
        mst.append((u, v, w))
        total += w
        for x, wx in g.adj[v]:
            if x not in seen:
                heap.push(wx, (v, x))
    return mst, total


def kruskal(g):
    """Kruskal's MST (minimum spanning forest if disconnected).
    Time: O(E log E) = O(E log V) dominated by sorting. Space: O(V + E)."""
    uf = UnionFind(g.vertices())
    mst, total = [], 0.0
    for u, v, w in sorted(g.edges(), key=lambda e: e[2]):
        if uf.union(u, v):
            mst.append((u, v, w))
            total += w
    return mst, total
