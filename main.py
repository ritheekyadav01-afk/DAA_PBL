"""Runs every module on the CSV data in data/ and writes outputs to report/."""
from src import apsp, dashboard, dp, experiments, greedy, mst, sssp
from src.graph import Graph


def fmt(g, path):
    # Time: O(len(path))
    return " -> ".join(g.names.get(v, v) for v in path)


def main():
    g = Graph.from_csv()
    print(f"Graph: {g.num_vertices()} stops, {g.num_edges()} roads (data is ESTIMATED placeholder)\n")

    pe, pw = mst.prim(g)
    ke, kw = mst.kruskal(g)
    print(f"[MST] Prim total = {pw:.1f} min, Kruskal total = {kw:.1f} min, match = {abs(pw - kw) < 1e-9}")

    src, dst = "S15", "S13"
    dist, prev = sssp.dijkstra(g, src)
    bd, _, neg = sssp.bellman_ford(g, src)
    path = sssp.reconstruct_path(prev, src, dst)
    print(f"[SSSP] Dijkstra {src}->{dst}: {dist[dst]:.1f} min via {fmt(g, path)}")
    print(f"       Bellman-Ford agrees = {all(abs(dist[v] - bd[v]) < 1e-9 for v in dist)}, neg cycle = {neg}")

    fw, nxt = apsp.floyd_warshall(g)
    vs = g.vertices()
    diam = max(((fw[u][v], u, v) for u in vs for v in vs), key=lambda t: t[0])
    print(f"[APSP] Floyd-Warshall agrees with Dijkstra = {abs(fw[src][dst] - dist[dst]) < 1e-9}; "
          f"longest shortest trip = {diam[0]:.1f} min ({diam[1]} -> {diam[2]})")

    shifts = greedy.load_shifts()
    one = greedy.select_shifts(shifts)
    drivers = greedy.assign_drivers(shifts)
    print(f"[Greedy] One driver can cover {len(one)}/{len(shifts)} shifts: {[s[0] for s in one]}")
    print(f"         All shifts need {len(drivers)} drivers")

    assignment, left = dp.assign_groups(dp.load_demand(), dp.load_fleet())
    print("[DP] Knapsack assignment (value = passengers x priority):")
    for sid, a in assignment.items():
        used = sum(x["passengers"] for x in a["groups"])
        print(f"     {sid}: {used}/{a['capacity']} seats, value {a['value']}, groups {[x['group_id'] for x in a['groups']]}")
    print(f"     Unassigned: {[x['group_id'] for x in left]}")

    print("\n[Experiments] benchmarking...")
    print("  saved", experiments.plot(experiments.run()))

    print("  saved", dashboard.save(dashboard.build_figure(g, pe, path)))


if __name__ == "__main__":
    main()
