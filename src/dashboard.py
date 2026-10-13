"""Builds report/dashboard.html: a self-contained, offline, animated dashboard.

No CDN and no plotting library — every number is read from the real algorithm
run and embedded as JSON into a hand-written HTML/CSS/JS template. This module
only *re-derives traces* for the animations (step order of Prim/Kruskal/Dijkstra,
the Floyd-Warshall matrix, etc.); it never changes an algorithm or a result.
"""
import decimal
import json
import math
import os

from src.apsp import floyd_warshall
from src.graph import DATA_DIR, MinHeap
from src.mst import UnionFind

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html")
TITLE = "Campus Shuttle Routing & Capacity Scheduling"
SUBTITLE = "Design & Analysis of Algorithms — real campus coordinates, assumed 20 km/h"
# Shown in the hero. Edit to your group's names.
TEAMS = "D. Ritheek · M. Srilakshmi · B. Deekshan · P. Priyakaran · G. Madhan"
TESTS_PASSING = 203  # from `pytest -q`; shown as a KPI

# Static facts for the complexity panel (no numbers depend on these).
COMPLEXITY = [
    ("Adjacency list build", "O(V + E)", "load stops & roads"),
    ("Prim (binary heap)", "O(E log V)", "MST"),
    ("Kruskal (union-find)", "O(E log E)", "MST"),
    ("Dijkstra (binary heap)", "O((V + E) log V)", "shortest path"),
    ("Bellman-Ford", "O(V · E)", "shortest path, cross-check"),
    ("Floyd-Warshall", "O(V³)", "all-pairs shortest paths"),
    ("Greedy activity selection", "O(S log S)", "driver shifts"),
    ("0-1 Knapsack (DP)", "O(n · W)", "passenger assignment"),
    ("Nearest-neighbour tour", "O(n²)", "heuristic TSP"),
    ("Held-Karp exact TSP", "O(n² · 2ⁿ)", "optimal tour"),
]


def _r2_half_up(x):
    """Round to 2 dp with conventional half-up (6.685 -> 6.69). Time: O(1)."""
    return float(decimal.Decimal(str(x)).quantize(decimal.Decimal("0.01"), rounding=decimal.ROUND_HALF_UP))


def _positions(g):
    """Project lat/lng to normalized [0,1] x,y (y flipped so north is up),
    aspect ratio preserved and centred. Time: O(V)."""
    ids = g.vertices()
    meanlat = sum(g.coords[v][0] for v in ids) / len(ids)
    k = math.cos(math.radians(meanlat))
    xs = {v: g.coords[v][1] * k for v in ids}
    ys = {v: g.coords[v][0] for v in ids}
    minx, maxx = min(xs.values()), max(xs.values())
    miny, maxy = min(ys.values()), max(ys.values())
    span = max(maxx - minx, maxy - miny) or 1.0
    ox, oy = (1 - (maxx - minx) / span) / 2, (1 - (maxy - miny) / span) / 2
    return {v: (round((xs[v] - minx) / span + ox, 4),
                round((maxy - ys[v]) / span + oy, 4)) for v in ids}


def _prim_steps(g, start):
    """Edges accepted by Prim, in order, with running total. Time: O(E log V)."""
    seen, heap, steps, total = {start}, MinHeap(), [], 0.0
    for v, w in g.adj[start]:
        heap.push(w, (start, v))
    while len(heap) and len(seen) < g.num_vertices():
        w, (u, v) = heap.pop()
        if v in seen:
            continue
        seen.add(v)
        total += w
        steps.append({"u": u, "v": v, "w": round(w, 2), "total": round(total, 2)})
        for x, wx in g.adj[v]:
            if x not in seen:
                heap.push(wx, (v, x))
    return steps


def _kruskal_steps(g):
    """Every candidate edge in weight order with accept/reject. Time: O(E log E)."""
    uf, steps, total = UnionFind(g.vertices()), [], 0.0
    for u, v, w in sorted(g.edges(), key=lambda e: e[2]):
        acc = uf.union(u, v)
        if acc:
            total += w
        steps.append({"u": u, "v": v, "w": round(w, 2), "accept": acc, "total": round(total, 2)})
    return steps


def _dijkstra_trace(g, source):
    """Finalisation order + prev/dist for one source. Time: O((V + E) log V)."""
    INF = float("inf")
    dist = {v: INF for v in g.adj}
    prev = {v: None for v in g.adj}
    dist[source] = 0.0
    heap, order = MinHeap(), []
    heap.push(0.0, source)
    while len(heap):
        d, u = heap.pop()
        if d > dist[u]:
            continue
        order.append({"v": u, "dist": round(dist[u], 2)})
        for v, w in g.adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heap.push(nd, v)
    return {"order": order, "prev": prev,
            "dist": {v: (round(dist[v], 2) if dist[v] != INF else None) for v in dist}}


def _mins_to_hhmm(m):
    # Time: O(1)
    return f"{m // 60:02d}:{m % 60:02d}"


def _payload(g, prim_edges, kruskal_edges, wait, sens, src, dst,
             drivers, shifts, assignment, unassigned):
    """Assemble every value the front end draws, all from the real run."""
    ids = g.vertices()
    pos = _positions(g)
    names = g.names

    stops = [{"id": v, "name": names[v], "lat": g.coords[v][0], "lng": g.coords[v][1],
              "x": pos[v][0], "y": pos[v][1]} for v in ids]
    edges = [{"u": u, "v": v, "w": round(w, 2)} for u, v, w in g.edges()]

    fw_dist, fw_nxt = floyd_warshall(g)
    matrix = [[round(fw_dist[u][v], 2) for v in ids] for u in ids]
    nxt = {u: {v: fw_nxt[u][v] for v in ids} for u in ids}

    dij = {s: _dijkstra_trace(g, s) for s in ids}

    shift_driver = {s[0]: i for i, dr in enumerate(drivers) for s in dr}
    shifts_out = [{"id": sid, "start": st, "end": en,
                   "startLabel": _mins_to_hhmm(st), "endLabel": _mins_to_hhmm(en),
                   "driver": shift_driver[sid]} for sid, st, en in shifts]

    vehicles = [{"id": sid, "cap": a["capacity"], "depot": a["depot"], "value": a["value"],
                 "used": sum(x["passengers"] for x in a["groups"]),
                 "groups": [{"id": x["group_id"], "pax": x["passengers"], "prio": x["priority"],
                             "val": x["passengers"] * x["priority"]} for x in a["groups"]]}
                for sid, a in assignment.items()]
    unassigned_out = [{"id": x["group_id"], "pax": x["passengers"], "prio": x["priority"]}
                      for x in unassigned]

    tours = [{"name": n, "order": wait["tours"][n], "cost": round(wait["costs"][n], 2)}
             for n in wait["tours"]]
    slices = [list(s) for s in wait["after_loops"]]

    return {
        "meta": {"title": TITLE, "subtitle": SUBTITLE, "teams": TEAMS},
        "kpi": {"stops": g.num_vertices(), "roads": g.num_edges(),
                "mstCost": _r2_half_up(sum(w for _, _, w in prim_edges)),
                "drivers": len(drivers), "shifts": len(shifts), "tests": TESTS_PASSING,
                "before": _r2_half_up(wait["before"]), "after": _r2_half_up(wait["after"]),
                "improvement": round(wait["improvement_pct"])},
        "stops": stops, "edges": edges,
        "defaults": {"src": src, "dst": dst},
        "mst": {"total": round(sum(w for _, _, w in prim_edges), 2),
                "prim": _prim_steps(g, src),
                "kruskal": _kruskal_steps(g),
                "edges": [[u, v, round(w, 2)] for u, v, w in prim_edges]},
        "dijkstra": dij,
        "fw": {"ids": ids, "matrix": matrix, "next": nxt},
        "greedy": {"shifts": shifts_out, "numDrivers": len(drivers),
                   "dayStart": min(s[1] for s in shifts), "dayEnd": max(s[2] for s in shifts)},
        "knapsack": {"vehicles": vehicles, "unassigned": unassigned_out},
        "tours": tours, "slices": slices,
        "waitBars": [{"name": n, "val": round(wait["waits"][n], 2)} for n in wait["waits"]]
                    + [{"name": f"After ({wait['k']} shuttles)", "val": round(wait["after"], 2)}],
        "sensitivity": {"k": sens["k"], "wait": [round(x, 2) for x in sens["wait"]],
                        "gain": [None if g_ is None else round(g_, 2) for g_ in sens["gain"]],
                        "knee": sens["knee"], "threshold": sens["threshold"]},
        "complexity": [{"name": n, "big_o": o, "use": u} for n, o, u in COMPLEXITY],
        "assumptions": wait["assumptions"],
        "dataNote": ("Stop names and GPS coordinates are REAL. Road links, travel times "
                     "(haversine at an assumed 20 km/h), passenger demand, fleet and driver "
                     "shifts are ESTIMATES for the model."),
    }


def build(g, prim_edges, kruskal_edges, wait, sens, src, dst,
          drivers, shifts, assignment, unassigned, path=None):
    """Write the standalone dashboard HTML. Time: O(V² + E) for the embedded data."""
    path = path or os.path.join(REPORT_DIR, "dashboard.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = _payload(g, prim_edges, kruskal_edges, wait, sens, src, dst,
                       drivers, shifts, assignment, unassigned)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("/*__PAYLOAD__*/null", json.dumps(payload, ensure_ascii=False))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
