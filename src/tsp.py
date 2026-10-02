"""Travel-salesman tours over a shortest-path distance table d[u][v] (closed tours)."""
INF = float("inf")


def tour_cost(order, d):
    """Cost of the closed tour visiting `order` and returning to its start.
    Time: O(n)."""
    if len(order) < 2:
        return 0.0
    return sum(d[order[i]][order[(i + 1) % len(order)]] for i in range(len(order)))


def nearest_neighbour(d, vertices, start):
    """Greedy tour: always go to the closest unvisited stop.
    Time: O(n^2). Not optimal; no constant-factor guarantee in general."""
    order, left = [start], set(vertices) - {start}
    while left:
        nxt = min(left, key=lambda v: d[order[-1]][v])
        order.append(nxt)
        left.remove(nxt)
    return order


def held_karp(d, vertices, start=None):
    """Exact TSP by bitmask DP. dp[mask][j] = cheapest path from `start` through
    the stops in `mask`, ending at j. Returns (optimal_cost, order).
    Time: O(n^2 * 2^n). Space: O(n * 2^n)."""
    vs = list(vertices)
    start = start if start is not None else vs[0]
    others = [v for v in vs if v != start]
    m = len(others)
    if m == 0:
        return 0.0, [start]
    full = 1 << m
    dp = [[INF] * m for _ in range(full)]
    par = [[-1] * m for _ in range(full)]
    for j in range(m):
        dp[1 << j][j] = d[start][others[j]]
    for mask in range(1, full):
        row = dp[mask]
        for j in range(m):
            cur = row[j]
            if cur == INF or not mask & (1 << j):
                continue
            dj = d[others[j]]
            for k in range(m):
                if mask & (1 << k):
                    continue
                nm = mask | (1 << k)
                c = cur + dj[others[k]]
                if c < dp[nm][k]:
                    dp[nm][k] = c
                    par[nm][k] = j
    last = min(range(m), key=lambda j: dp[full - 1][j] + d[others[j]][start])
    best = dp[full - 1][last] + d[others[last]][start]
    order, mask, j = [], full - 1, last
    while j != -1:
        order.append(others[j])
        pj = par[mask][j]
        mask ^= 1 << j
        j = pj
    order.append(start)
    order.reverse()
    return best, order
