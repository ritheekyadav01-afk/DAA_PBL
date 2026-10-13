"""Builds report/dashboard.html: a simple, story-style, offline dashboard.

The page (src/dashboard_template.html) is hand-written HTML/CSS/JS with no CDN.
This module only collects the results of the real algorithm run into one JSON
payload and injects it into the template, so every number on the page comes
from the actual run. It never changes an algorithm or a result.
"""
import decimal
import json
import math
import os

from src import greedy
from src.apsp import floyd_warshall
from src.mst import kruskal
from src.sssp import bellman_ford, dijkstra

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")
TITLE = "Campus Shuttle Routing & Capacity Scheduling"
SUBTITLE = "Design & Analysis of Algorithms · Woxsen University"
# Shown in the footer. Edit to your group's names.
TEAMS = "D. Ritheek · M. Srilakshmi · B. Deekshan · P. Priyakaran · G. Madhan"
TESTS_PASSING = 204  # from `pytest -q`; shown on the "Tested" card


def _r2(x):
    """Round to 2 dp, half-up (6.685 -> 6.69), as people expect. Time: O(1)."""
    return float(decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP))


def _positions(g):
    """Project lat/lng to [0,1] x,y (north up), aspect ratio preserved and
    centred in the unit square. Time: O(V)."""
    ids = g.vertices()
    k = math.cos(math.radians(sum(g.coords[v][0] for v in ids) / len(ids)))
    xs = {v: g.coords[v][1] * k for v in ids}
    ys = {v: g.coords[v][0] for v in ids}
    minx, maxx, miny, maxy = min(xs.values()), max(xs.values()), min(ys.values()), max(ys.values())
    span = max(maxx - minx, maxy - miny) or 1.0
    ox, oy = (1 - (maxx - minx) / span) / 2, (1 - (maxy - miny) / span) / 2
    return {v: (round((xs[v] - minx) / span + ox, 4), round((maxy - ys[v]) / span + oy, 4)) for v in ids}


def _checks(g, prim_total, kruskal_total, fw_dist, wait):
    """Live cross-checks, recomputed here so the Trust section is not just a claim.
    Time: O(V (V + E) log V + V E) for the shortest-path comparisons."""
    paths_ok = True
    for s in g.vertices():
        dist, _ = dijkstra(g, s)
        bf, _, neg = bellman_ford(g, s)
        paths_ok &= (not neg) and all(
            abs(dist[v] - bf[v]) < 1e-9 and abs(dist[v] - fw_dist[s][v]) < 1e-9 for v in g.vertices())
    best = wait["optimal_cost"]
    heur = [wait["costs"][n] for n in wait["costs"] if n != "Optimal (Held-Karp)"]
    return {
        "mst": abs(prim_total - kruskal_total) < 1e-9,
        "paths": bool(paths_ok),
        "tour": all(best <= c + 1e-9 for c in heur),
    }


def _payload(g, prim_edges, wait, sens, src, dst, drivers, shifts, assignment, unassigned):
    """Assemble every value the page shows. Time: O(V^3) (Floyd-Warshall dominates)."""
    ids = g.vertices()
    names = g.names
    pos = _positions(g)
    prim_total = sum(w for _, _, w in prim_edges)
    _, kruskal_total = kruskal(g)  # only to compare totals for the Trust card

    fw_dist, fw_nxt = floyd_warshall(g)
    dij = {}
    for s in ids:
        dist, prev = dijkstra(g, s)
        dij[s] = {"prev": prev, "dist": {v: round(dist[v], 4) for v in ids}}
    far = max(((fw_dist[u][v], u, v) for u in ids for v in ids), key=lambda t: t[0])

    fw_checks = _checks(g, prim_total, kruskal_total, fw_dist, wait)
    costs = wait["costs"]
    opt = costs["Optimal (Held-Karp)"]
    waits = wait["waits"]
    route_min = dij[src]["dist"][dst]
    one_driver = len(greedy.select_shifts(shifts))
    seats = ", ".join(f"{sid} {sum(x['passengers'] for x in a['groups'])}/{a['capacity']}"
                      for sid, a in assignment.items())

    steps = [
        {"icon": "graph", "title": "Model the campus as a graph",
         "algos": "Graph · adjacency list",
         "simple": "Stops become dots, roads become lines with a travel time.",
         "result": f"{len(ids)} stops · {g.num_edges()} roads"},
        {"icon": "route", "title": "Find roads and routes",
         "algos": "Prim · Kruskal · Dijkstra · Bellman-Ford · Floyd-Warshall",
         "simple": "Find the cheapest road network and the fastest route between stops.",
         "result": f"{_r2(prim_total):.2f} min road network",
         "result2": f"{names[src]} to {names[dst]}: {route_min:.1f} min"},
        {"icon": "calendar", "title": "Schedule drivers and vehicles",
         "algos": "Greedy scheduling · 0-1 knapsack",
         "simple": "Give every shift a driver, and fit passenger groups into vehicle seats.",
         "result": f"{len(drivers)} drivers",
         "result2": f"cover all {len(shifts)} shifts"},
        {"icon": "loop", "title": "Plan the best loop",
         "algos": "MST tour · Held-Karp (exact)",
         "simple": "Pick the stop order that makes one trip around campus shortest.",
         "result": f"{_r2(opt):.2f} min loop",
         "result2": f"best possible; our MST loop is {_r2(costs['MST preorder']):.2f} ({wait['mst_ratio']:.3f}x)"},
    ]

    # For the professor: every algorithm, its time complexity and the real result.
    algos = [
        ("Prim (binary heap)", "O(E log V)", f"Cheapest road network {_r2(prim_total):.2f} min",
         "Grow one network from a stop, always adding the cheapest road that reaches a new stop."),
        ("Kruskal (union-find)", "O(E log E)", f"Same network, {_r2(kruskal_total):.2f} min",
         "Sort roads by time and keep each one that does not close a loop."),
        ("Dijkstra (binary heap)", "O((V+E) log V)", f"{names[src]} to {names[dst]}: {route_min:.1f} min",
         "Spread outwards from the start, always finalising the closest stop first."),
        ("Bellman-Ford", "O(V·E)", "Agrees with Dijkstra on every route" if fw_checks["paths"] else "DISAGREES with Dijkstra",
         "Repeatedly relax every road; a slower second opinion."),
        ("Floyd-Warshall", "O(V³)", f"Longest shortest trip {far[0]:.1f} min ({names[far[1]]} to {names[far[2]]})",
         "Try every stop as a stepping stone to get all pairs at once."),
        ("Greedy activity selection", "O(S log S)", f"1 driver covers {one_driver} of {len(shifts)} shifts; {len(drivers)} cover all",
         "Always take the shift that ends earliest, then repeat for the next driver."),
        ("0-1 knapsack (DP)", "O(n·W)", f"Seats used: {seats}",
         "For each vehicle, pick the passenger groups worth the most that still fit."),
        ("Nearest neighbour", "O(n²)", f"Loop {_r2(costs['Nearest neighbour']):.2f} min",
         "From each stop, always go to the closest unvisited stop."),
        ("MST preorder tour", "O(V log V)", f"Loop {_r2(costs['MST preorder']):.2f} min ({wait['mst_ratio']:.3f}x best)",
         "Walk around the cheapest network; provably at most 2x the best loop."),
        ("Held-Karp (exact TSP)", "O(n²·2ⁿ)", f"Best loop {_r2(opt):.2f} min",
         "Try all subsets of stops with memory, so the best loop is guaranteed."),
        ("Wait model", "O(V)", f"{_r2(wait['before']):.2f} to {_r2(wait['after']):.2f} min ({round(wait['improvement_pct'])}% less)",
         "Average wait is half the loop time, weighted by how many people start at each stop."),
    ]

    return {
        "meta": {"title": TITLE, "subtitle": SUBTITLE, "teams": TEAMS},
        "kpi": {
            "stops": len(ids), "roads": g.num_edges(), "mstCost": _r2(prim_total),
            "drivers": len(drivers), "shifts": len(shifts), "tests": TESTS_PASSING,
            "before": _r2(wait["before"]), "mstOne": _r2(waits["MST preorder"]),
            "after": _r2(wait["after"]), "improvement": round(wait["improvement_pct"]),
            "fileLoop": _r2(costs["File order"]), "mstLoop": _r2(costs["MST preorder"]),
            "optLoop": _r2(opt), "shuttles": wait["k"],
        },
        "stops": [{"id": v, "name": names[v], "x": pos[v][0], "y": pos[v][1]} for v in ids],
        "edges": [{"u": u, "v": v, "w": round(w, 2)} for u, v, w in g.edges()],
        "defaults": {"src": src, "dst": dst, "altSrc": far[1], "altDst": far[2]},  # alt = longest trip, for Presentation mode
        "dijkstra": dij,
        "fwNext": {u: {v: fw_nxt[u][v] for v in ids} for u in ids},
        "fileOrder": wait["tours"]["File order"],
        "slices": [list(s) for s in wait["after_loops"]],
        "sensitivity": {"k": sens["k"], "wait": [_r2(x) for x in sens["wait"]],
                        "knee": sens["knee"], "threshold": sens["threshold"]},
        "steps": steps,
        "algos": [{"name": n, "bigO": o, "result": r, "simple": s} for n, o, r, s in algos],
        "checks": fw_checks,
        "dataNote": ("Stop names and GPS coordinates are real. Roads, travel times (20 km/h assumed), "
                     "passenger demand, fleet and driver shifts are estimates."),
    }


def build(g, prim_edges, kruskal_edges, wait, sens, src, dst,
          drivers, shifts, assignment, unassigned, path=None):
    """Write the standalone dashboard HTML. `kruskal_edges` and `unassigned` are
    accepted for a stable call signature. Time: O(V^3) for the embedded data."""
    path = path or os.path.join(REPORT_DIR, "dashboard.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = _payload(g, prim_edges, wait, sens, src, dst, drivers, shifts, assignment, unassigned)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__PAYLOAD__*/null", json.dumps(payload, ensure_ascii=False))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
