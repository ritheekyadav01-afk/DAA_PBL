"""All-pairs shortest paths: Floyd-Warshall."""
INF = float("inf")


def floyd_warshall(g):
    """Returns (dist, nxt) dicts-of-dicts; nxt supports path reconstruction.
    Time: O(V^3). Space: O(V^2)."""
    vs = g.vertices()
    dist = {u: {v: (0.0 if u == v else INF) for v in vs} for u in vs}
    nxt = {u: {v: None for v in vs} for u in vs}
    for u in vs:
        for v, w in g.adj[u]:
            if w < dist[u][v]:
                dist[u][v] = w
                nxt[u][v] = v
    for k in vs:
        dk = dist[k]
        for i in vs:
            dik = dist[i][k]
            if dik == INF:
                continue
            di = dist[i]
            for j in vs:
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
                    nxt[i][j] = nxt[i][k]
    return dist, nxt


def fw_path(nxt, u, v):
    """Reconstruct a path from the Floyd-Warshall next-hop table. Time: O(V)."""
    if nxt[u][v] is None and u != v:
        return []
    path = [u]
    while u != v:
        u = nxt[u][v]
        path.append(u)
    return path
