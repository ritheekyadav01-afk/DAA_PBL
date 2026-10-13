import itertools
import math
import random

import pytest

from src.apsp import floyd_warshall
from src.graph import Graph
from src.mst import kruskal, prim
from src.sssp import bellman_ford, dijkstra
from src.tsp import held_karp, nearest_neighbour, tour_cost
from src.wait_model import mst_tour

SEEDS = range(50)


def random_graph(seed):
    rnd = random.Random(seed)
    n = rnd.randint(5, 25)
    g = Graph()
    for i in range(n):
        g.add_vertex(i)
    for i in range(1, n):  # random spanning tree keeps it connected
        g.add_edge(rnd.randrange(i), i, round(rnd.uniform(0.1, 10), 2))
    for _ in range(rnd.randint(0, 2 * n)):
        u, v = rnd.randrange(n), rnd.randrange(n)
        if u != v:
            g.add_edge(u, v, round(rnd.uniform(0.1, 10), 2))
    return g


@pytest.mark.parametrize("seed", SEEDS)
def test_shortest_paths_agree(seed):
    g = random_graph(seed)
    fw, _ = floyd_warshall(g)
    for s in g.vertices():
        dj, _ = dijkstra(g, s)
        bf, _, neg = bellman_ford(g, s)
        assert not neg
        for v in g.vertices():
            assert dj[v] == pytest.approx(bf[v])
            assert dj[v] == pytest.approx(fw[s][v])


@pytest.mark.parametrize("seed", SEEDS)
def test_prim_equals_kruskal(seed):
    g = random_graph(seed)
    pe, pc = prim(g)
    ke, kc = kruskal(g)
    assert pc == pytest.approx(kc)
    assert len(pe) == len(ke) == g.num_vertices() - 1


def metric(seed, n):
    g = random_graph(seed)
    # take the first n vertices of a connected graph's metric closure
    d, _ = floyd_warshall(g)
    return d, g.vertices()[:n]


@pytest.mark.parametrize("seed", SEEDS)
def test_held_karp_beats_heuristics(seed):
    g = random_graph(seed)
    d, _ = floyd_warshall(g)
    vs = g.vertices()[:10]
    start = vs[0]
    best, order = held_karp(d, vs, start)
    assert sorted(order) == sorted(vs)
    assert tour_cost(order, d) == pytest.approx(best)
    assert best <= tour_cost(nearest_neighbour(d, vs, start), d) + 1e-9
    assert best <= tour_cost(vs, d) + 1e-9
    sub = Graph()  # MST over the same stops using the metric closure
    for v in vs:
        sub.add_vertex(v)
    for u, v in itertools.combinations(vs, 2):
        sub.add_edge(u, v, d[u][v])
    mst_edges, _ = prim(sub)
    mt = mst_tour(mst_edges, d, start)
    assert best <= tour_cost(mt, d) + 1e-9
    assert tour_cost(mt, d) <= 2 * best + 1e-9  # classic 2-approximation


def test_held_karp_matches_brute_force():
    d, vs = metric(3, 7)
    best, _ = held_karp(d, vs, vs[0])
    brute = min(tour_cost([vs[0], *p], d) for p in itertools.permutations(vs[1:]))
    assert best == pytest.approx(brute)


def test_held_karp_on_real_campus():
    g = Graph.from_csv()
    d, _ = floyd_warshall(g)
    vs = g.vertices()
    best, order = held_karp(d, vs, vs[0])
    assert len(order) == len(vs) == 14
    assert best <= tour_cost(vs, d) + 1e-9
    assert best <= tour_cost(nearest_neighbour(d, vs, vs[0]), d) + 1e-9


@pytest.mark.parametrize("seed", SEEDS)
def test_knapsack_matches_brute_force(seed):
    from src.dp import knapsack
    rnd = random.Random(seed)
    n = rnd.randint(1, 10)
    weights = [rnd.randint(1, 12) for _ in range(n)]
    values = [rnd.randint(1, 30) for _ in range(n)]
    cap = rnd.randint(0, 30)
    best, chosen = knapsack(weights, values, cap)
    brute = max(sum(values[i] for i in range(n) if m >> i & 1)
                for m in range(1 << n)
                if sum(weights[i] for i in range(n) if m >> i & 1) <= cap)
    assert best == brute
    assert sum(weights[i] for i in chosen) <= cap
    assert sum(values[i] for i in chosen) == best


def test_dashboard_generated_with_key_numbers(tmp_path):
    """The offline dashboard is built from the real run and embeds the headline
    numbers (MST 5.81, wait 6.69 -> 2.03), with the JSON payload injected."""
    from src import dashboard, dp, greedy, mst, sensitivity, wait_model
    g = Graph.from_csv()
    pe, _ = mst.prim(g)
    ke, _ = mst.kruskal(g)
    by_name = {n: v for v, n in g.names.items()}
    src, dst = by_name["Bus Stop"], by_name["Race Arena"]
    wait = wait_model.compare(g, pe, src)
    sens = sensitivity.run(g, pe, src)
    shifts = greedy.load_shifts()
    drivers = greedy.assign_drivers(shifts)
    assignment, left = dp.assign_groups(dp.load_demand(), dp.load_fleet())
    out = tmp_path / "dash.html"
    dashboard.build(g, pe, ke, wait, sens, src, dst, drivers, shifts, assignment, left, path=str(out))
    html = out.read_text(encoding="utf-8")
    assert out.exists() and len(html) > 20000
    for number in ("5.81", "6.69", "2.03"):
        assert number in html, f"missing key number {number}"
    assert "Campus Shuttle" in html
    assert "/*__PAYLOAD__*/null" not in html  # payload actually injected
