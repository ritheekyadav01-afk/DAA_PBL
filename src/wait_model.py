"""Average passenger wait model: naive baseline vs optimized service.

Assumptions (also shown on the dashboard):
- Passengers arrive uniformly in time, so a stop served by a loop of length T
  min has an average wait of T/2 min.
- Each stop is weighted by passengers originating there (data/demand.csv).
- Loop time = sum of shortest-path times between consecutive stops (edge time =
  haversine distance at an assumed shuttle speed; no dwell time modeled).
"""
from src.apsp import floyd_warshall
from src.dp import load_demand, load_fleet


def stop_weights(demand):
    """Passengers per origin stop. Time: O(G)."""
    w = {}
    for r in demand:
        w[r["origin_stop"]] = w.get(r["origin_stop"], 0) + r["passengers"]
    return w


def loop_time(order, d):
    """Cyclic loop time over `order` using distance table d. Time: O(len(order))."""
    if len(order) < 2:
        return 0.0
    return sum(d[order[i]][order[(i + 1) % len(order)]] for i in range(len(order)))


def mst_tour(mst_edges, d, start):
    """Preorder walk of the MST from `start` (nearest child first): a classic
    2-approximation visiting order. Time: O(V^2) worst case for child sorting
    with O(V) children per node, typically O(V log V)."""
    adj = {}
    for u, v, _ in mst_edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    order, seen = [], set()

    def dfs(u):
        seen.add(u)
        order.append(u)
        for v in sorted(adj.get(u, []), key=lambda x: d[u][x]):
            if v not in seen:
                dfs(v)

    dfs(start)
    return order


def split_even(order, k):
    """Split a visiting order into k contiguous chunks. Time: O(V)."""
    k = max(1, min(k, len(order)))
    size, extra = divmod(len(order), k)
    out, i = [], 0
    for j in range(k):
        n = size + (1 if j < extra else 0)
        out.append(order[i:i + n])
        i += n
    return out


def weighted_wait(loops, d, w):
    """Passenger-weighted mean of T_loop/2 over loops. Time: O(V)."""
    tot = sum(w.get(s, 0) for lp in loops for s in lp)
    if tot == 0:
        return 0.0
    return sum(loop_time(lp, d) / 2 * sum(w.get(s, 0) for s in lp) for lp in loops) / tot


def compare(g, mst_edges, start):
    """Before/after average wait. Time: O(V^3) (Floyd-Warshall) + O(V^2)."""
    d, _ = floyd_warshall(g)
    w = stop_weights(load_demand())
    k = len(load_fleet())
    naive = g.vertices()  # stops in stops.csv order, one shuttle
    tour = mst_tour(mst_edges, d, start)
    before = weighted_wait([naive], d, w)
    route_only = weighted_wait([tour], d, w)
    after_loops = split_even(tour, k)
    after = weighted_wait(after_loops, d, w)
    return {
        "before": before, "route_only": route_only, "after": after,
        "improvement_pct": 100 * (before - after) / before if before else 0.0,
        "naive_loop": naive, "naive_loop_min": loop_time(naive, d),
        "tour": tour, "after_loops": after_loops, "k": k,
        "assumptions": [
            "Passengers arrive uniformly, so average wait = loop time / 2",
            "Stops weighted by passengers in demand.csv (all estimated)",
            f"Before: 1 shuttle visits stops in stops.csv order ({naive[0]}..{naive[-1]}) and repeats",
            "Route only: 1 shuttle on the MST preorder tour",
            f"After: {k} fleet shuttles run concurrently, each looping one contiguous slice of the MST tour",
            "Shift schedule: greedy driver assignment staffs the fleet; wait uses steady-state headways",
        ],
    }
