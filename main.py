"""Runs every module on the CSV data in data/ and writes outputs to report/."""
from src import apsp, dashboard, dp, experiments, greedy, mst, sensitivity, sssp, wait_model
from src.graph import Graph


def fmt(g, path):
    # Time: O(len(path))
    return " -> ".join(g.names.get(v, v) for v in path)


def main():
    g = Graph.from_csv()
    print(f"Graph: {g.num_vertices()} stops, {g.num_edges()} roads (edges/demand/fleet are ESTIMATES)\n")

    pe, pw = mst.prim(g)
    ke, kw = mst.kruskal(g)
    print(f"[MST] Prim total = {pw:.1f} min, Kruskal total = {kw:.1f} min, match = {abs(pw - kw) < 1e-9}")

    by_name = {n: v for v, n in g.names.items()}
    src, dst = by_name["Bus Stop"], by_name["Race Arena"]
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
        print(f"     {sid} (depot {a['depot']}): {used}/{a['capacity']} seats, value {a['value']}, groups {[x['group_id'] for x in a['groups']]}")
    print(f"     Unassigned: {[x['group_id'] for x in left]}")

    print("\n[Experiments] benchmarking...")
    print("  saved", experiments.plot(experiments.run()))

    wait = wait_model.compare(g, pe, src)
    print("[TSP] closed-tour cost over shortest-path times (start = Bus Stop):")
    for name, c in wait["costs"].items():
        print(f"      {name:<22} {c:6.2f} min  ({c / wait['optimal_cost']:.3f}x optimal)")
    print(f"      MST approximation ratio = {wait['mst_ratio']:.3f} (theory: <= 2.000)")
    print("      Optimal order:", fmt(g, wait["tours"]["Optimal (Held-Karp)"]))
    print(f"[Wait] avg wait: file-order {wait['before']:.2f}, nearest-neighbour "
          f"{wait['waits']['Nearest neighbour']:.2f}, MST {wait['route_only']:.2f}, optimal "
          f"{wait['waits']['Optimal (Held-Karp)']:.2f}, after (3 shuttles) {wait['after']:.2f} min -> {wait['improvement_pct']:.0f}% improvement")
    for a in wait["assumptions"]:
        print("       -", a)
    sens = sensitivity.run(g, pe, src)
    print("[Fleet] avg wait vs number of shuttles (MST tour slices):")
    for k, wt, gain in zip(sens["k"], sens["wait"], sens["gain"]):
        print(f"      {k} shuttle(s): {wt:.2f} min" + ("" if gain is None else f"  (saves {gain:.2f} vs {k - 1})"))
    if sens["knee"]:
        print(f"      Improvement per extra shuttle first drops below {sens['threshold']} min at "
              f"{sens['knee']} shuttles")
    else:
        print(f"      Improvement per extra shuttle never drops below {sens['threshold']} min up to {sens['k'][-1]}")
    print("  saved", sensitivity.plot(sens))
    fig, data = dashboard.build_figure(g, pe, wait, src, dst, sens)
    print("  saved", dashboard.save(fig, data))

if __name__ == "__main__":
    main()
