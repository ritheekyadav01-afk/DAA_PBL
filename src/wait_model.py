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
from src.tsp import held_karp, nearest_neighbour, tour_cost


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
    """Before/after average wait plus tour costs for every tour heuristic.
    Time: O(V^3) Floyd-Warshall + O(V^2 * 2^V) Held-Karp (dominant for V = 14)."""
    d, _ = floyd_warshall(g)
    w = stop_weights(load_demand())
    k = len(load_fleet())
    vs = g.vertices()
    tours = {
        "File order": vs,  # stops in stops.csv order
        "Nearest neighbour": nearest_neighbour(d, vs, start),
        "MST preorder": mst_tour(mst_edges, d, start),
    }
    opt_cost, tours["Optimal (Held-Karp)"] = held_karp(d, vs, start)
    costs = {n: tour_cost(t, d) for n, t in tours.items()}
    waits = {n: weighted_wait([t], d, w) for n, t in tours.items()}
    tour = tours["MST preorder"]
    after_loops = split_even(tour, k)
    after = weighted_wait(after_loops, d, w)
    before = waits["File order"]
    return {
        "tours": tours, "costs": costs, "waits": waits, "optimal_cost": opt_cost,
        "mst_ratio": costs["MST preorder"] / opt_cost if opt_cost else 1.0,
        "before": before, "route_only": waits["MST preorder"], "after": after,
        "improvement_pct": 100 * (before - after) / before if before else 0.0,
        "naive_loop": vs, "naive_loop_min": costs["File order"],
        "tour": tour, "after_loops": after_loops, "k": k,
        "assumptions": [
            "Passengers arrive uniformly, so average wait = loop time / 2",
            "Stops weighted by passengers in demand.csv (all estimated)",
            f"Before: 1 shuttle visits stops in stops.csv order ({vs[0]}..{vs[-1]}) and repeats",
            "Nearest neighbour / MST preorder / Optimal: 1 shuttle on that closed tour",
            "Optimal = Held-Karp exact TSP over shortest-path distances",
            f"After: {k} fleet shuttles run concurrently, each looping one contiguous slice of the MST tour",
            "Shift schedule: greedy driver assignment staffs the fleet; wait uses steady-state headways",
        ],
    }
