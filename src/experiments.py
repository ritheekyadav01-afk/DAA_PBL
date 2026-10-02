"""Empirical runtime vs graph size, plotted against theoretical complexity."""
import math
import os
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.apsp import floyd_warshall
from src.graph import Graph
from src.mst import kruskal, prim
from src.sssp import bellman_ford, dijkstra

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")


def random_graph(n, avg_degree=4, seed=0):
    """Connected random graph: random spanning tree + extra edges.
    Time: O(n + E)."""
    rnd = random.Random(seed)
    g = Graph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(1, n):
        g.add_edge(rnd.randrange(i), i, rnd.uniform(1, 10))
    for _ in range(max(0, n * avg_degree // 2 - (n - 1))):
        u, v = rnd.randrange(n), rnd.randrange(n)
        if u != v:
            g.add_edge(u, v, rnd.uniform(1, 10))
    return g


def timeit(fn, repeats=3):
    """Best-of-k wall time in seconds. Time: O(repeats * cost(fn))."""
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t)
    return best


def run(sizes=(50, 100, 200, 400, 800, 1600), fw_max=200):
    """Benchmark all algorithms. Time: dominated by the largest runs above.
    Returns {algo: [(n, E, seconds)]}."""
    res = {k: [] for k in ("Prim", "Kruskal", "Dijkstra", "Bellman-Ford", "Floyd-Warshall")}
    for n in sizes:
        g = random_graph(n)
        e = g.num_edges()
        src = 0
        res["Prim"].append((n, e, timeit(lambda: prim(g))))
        res["Kruskal"].append((n, e, timeit(lambda: kruskal(g))))
        res["Dijkstra"].append((n, e, timeit(lambda: dijkstra(g, src))))
        res["Bellman-Ford"].append((n, e, timeit(lambda: bellman_ford(g, src), 1)))
        if n <= fw_max:
            res["Floyd-Warshall"].append((n, e, timeit(lambda: floyd_warshall(g), 1)))
    return res


THEORY = {
    "Prim": ("O(E log V)", lambda n, e: e * math.log2(n)),
    "Kruskal": ("O(E log E)", lambda n, e: e * math.log2(max(e, 2))),
    "Dijkstra": ("O((V+E) log V)", lambda n, e: (n + e) * math.log2(n)),
    "Bellman-Ford": ("O(VE)", lambda n, e: n * e),
    "Floyd-Warshall": ("O(V^3)", lambda n, e: n ** 3),
}


def plot(res, path=None):
    """One log-log panel per algorithm: measured points vs theoretical curve
    scaled by a least-squares constant (in log space). Time: O(total points)."""
    path = path or os.path.join(REPORT_DIR, "runtime_vs_complexity.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5))
    for ax, (name, pts) in zip(axes.flat, res.items()):
        label, f = THEORY[name]
        ns = np.array([p[0] for p in pts])
        ts = np.array([p[2] for p in pts])
        th = np.array([f(p[0], p[1]) for p in pts])
        c = math.exp(np.mean(np.log(ts) - np.log(th)))
        ax.loglog(ns, ts, "o-", color="#2a78d6", label="measured")
        ax.loglog(ns, c * th, "--", color="#eb6834", label=f"{label} (scaled)")
        ax.set_title(name)
        ax.set_xlabel("vertices V")
        ax.set_ylabel("seconds")
        ax.legend()
        ax.grid(alpha=0.3)
    for ax in list(axes.flat)[len(res):]:
        ax.axis("off")
    fig.suptitle("Runtime vs graph size (random connected graphs, avg degree 4)")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path
