"""Single-source shortest paths: Dijkstra (heapq) and Bellman-Ford."""
from src.graph import MinHeap

INF = float("inf")


def dijkstra(g, source):
    """Dijkstra with lazy-deletion binary heap; non-negative weights only.
    Returns (dist, prev). Time: O((V + E) log V). Space: O(V)."""
    dist = {v: INF for v in g.adj}
    prev = {v: None for v in g.adj}
    dist[source] = 0.0
    heap = MinHeap()
    heap.push(0.0, source)
    while len(heap):
        d, u = heap.pop()
        if d > dist[u]:
            continue
        for v, w in g.adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heap.push(nd, v)
    return dist, prev


def bellman_ford(g, source):
    """Bellman-Ford with early exit; handles negative weights.
    Returns (dist, prev, has_negative_cycle). Time: O(V * E). Space: O(V)."""
    dist = {v: INF for v in g.adj}
    prev = {v: None for v in g.adj}
    dist[source] = 0.0
    arcs = [(u, v, w) for u, nbrs in g.adj.items() for v, w in nbrs]
    for _ in range(len(g.adj) - 1):
        changed = False
        for u, v, w in arcs:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                changed = True
        if not changed:
            break
    neg = any(dist[u] + w < dist[v] for u, v, w in arcs)
    return dist, prev, neg


def reconstruct_path(prev, source, target):
    """Walk predecessor map back from target. Time: O(V)."""
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path if path and path[0] == source else []
