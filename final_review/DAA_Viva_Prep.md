# DAA Final Review: Viva Prep (Campus Shuttle Routing & Capacity Scheduling)

**Team:** D. Ritheek (25WU0102057), M. Srilakshmi (25WU0102140), B. Deekshan (25WU0102037), P. Priyakaran (25WU0101090), G. Madhan (25WU0102344)

## 20-second pitch
I modelled 14 real Woxsen campus stops as a weighted graph and used MST, Dijkstra/Bellman-Ford, Floyd-Warshall, greedy scheduling, knapsack DP and Held-Karp TSP to design a better shuttle loop. Average wait drops from 6.69 min (one shuttle, file order) to 2.03 min (three shuttles on an MST-based tour), a 70% improvement.

## Numbers to remember
| Item | Value |
|---|---|
| Graph | 14 stops, 22 edges, 20 km/h assumed |
| MST (Prim = Kruskal) | 5.8 min total |
| Dijkstra Bus Stop to Race Arena | 3.3 min via Care and Cure, Academic Blocks, Library, Oval |
| Longest shortest trip (Floyd-Warshall) | 4.3 min, Main Gate to Cricket Ground |
| Greedy | 1 driver covers 8 of 18 shifts; 4 drivers staff all shifts |
| Knapsack | BUS-1 30/30 seats (value 125), BUS-2 19/20 (69), VAN-1 9/12 (36) |
| TSP | file order 13.37, nearest neighbour 10.11, MST preorder 10.11, optimal 9.92 min |
| MST tour vs optimal | 1.019x (theory bound 2x) |
| Average wait | 6.69 baseline, 5.05 one shuttle on MST tour, 2.03 with 3 shuttles |
| Fleet sensitivity | 1: 5.05, 2: 3.91, 3: 2.03, 4: 1.75, 5: 1.26, 6: 1.12 min |
| Tests | 202 pass |

## Likely questions and answers

**1. Why a graph?** Stops are vertices and roads are edges weighted by travel time. Every question (cheapest connection, fastest route, all pairs, tour) becomes a standard graph problem.

**2. Prim vs Kruskal: how do they differ and when is each better?** Prim grows one tree from a start vertex using a priority queue: O(E log V), good for dense graphs. Kruskal sorts edges and adds the cheapest that does not form a cycle, using union-find: O(E log E), good for sparse graphs. Both gave 5.8 min, which is a built-in correctness check.

**3. Why is the MST useful for a shuttle?** It is the cheapest backbone of roads connecting every stop, and a preorder walk of it gives a tour at most 2x optimal (when distances satisfy the triangle inequality). Here it came out at 1.019x.

**4. Dijkstra vs Bellman-Ford?** Dijkstra is O((V+E) log V) but needs non-negative weights. Bellman-Ford is O(VE), handles negative weights and detects negative cycles. Travel times are never negative, so Dijkstra is the right tool. I ran both and they agree, and Bellman-Ford confirmed there is no negative cycle.

**5. Why Floyd-Warshall when you already have Dijkstra?** Floyd-Warshall gives all pairs at once in O(V^3), a good fit for the 14x14 table the TSP and wait model need. Running Dijkstra from every source would also work (O(V(V+E) log V)); I verified the two match.

**6. Why does Floyd-Warshall work?** It is dynamic programming: after considering intermediate vertices 1..k, d[i][j] is the shortest path using only those intermediates. For each k, d[i][j] = min(d[i][j], d[i][k] + d[k][j]).

**7. Which greedy strategy did you use and why is it correct?** Earliest-finish-time-first for selecting the maximum number of non-overlapping shifts for one driver. It is optimal by an exchange argument: swapping any optimal solution's first shift for the earliest-finishing one never reduces the count. For staffing all shifts, I repeat that selection on the remaining shifts, one driver at a time (interval-partitioning style); it needed 4 drivers. Be ready to say this is a greedy heuristic: the true minimum equals the maximum number of shifts overlapping at one moment, and 4 is consistent with that for this data.

**8. Why DP for the vehicle assignment, not greedy?** It is a 0-1 knapsack: each passenger group is either taken or not (cannot split a group), with capacity as weight and passengers x priority as value. Greedy by value density can be suboptimal for 0-1 knapsack, while DP is exact in O(nW).

**9. Why is TSP hard and how did you handle it?** TSP is NP-hard. For 14 stops, Held-Karp (bitmask DP, O(n^2 2^n)) gives the exact optimum in practice. For larger campuses that blows up, so I compare against nearest neighbour O(n^2) and the MST 2-approximation O(V log V), and show they land within 2% of optimal here.

**10. Is the MST tour guaranteed to be within 2x?** Yes if distances obey the triangle inequality, which shortest-path distances do. The doubled MST is an Eulerian walk of cost 2 x MST, and shortcutting repeated vertices cannot increase cost. Optimal TSP is at least MST cost, so tour <= 2 x optimal.

**11. How do you compute average wait?** For a loop of length T min and uniform arrivals, average wait at a stop is T/2. Stops are weighted by passengers originating there. Three shuttles split the MST tour into contiguous slices that run concurrently, which shortens each loop.

**12. Why three shuttles?** The fleet-sensitivity sweep shows 2 to 3 shuttles saves 1.88 min but 3 to 4 saves only 0.28 min, so 3 is the knee of the curve and matches the fleet file's three vehicles.

**13. How did you validate correctness?** 202 tests, mostly cross-checks: Prim vs Kruskal, Dijkstra vs Bellman-Ford vs Floyd-Warshall, Held-Karp vs brute-force permutations, knapsack DP vs brute-force subsets, and Held-Karp never losing to the heuristics, over many random seeds.

**14. How did you check the complexity empirically?** The benchmark in `report/runtime_vs_complexity.png` times the algorithms on graphs from 50 to 1600 nodes, with Floyd-Warshall capped at 200 because of O(V^3). The curves follow the theoretical growth.

**15. Is your data real? (answer this honestly, it will come up)** Stop names and GPS coordinates are real. The road set (which stops connect), the 20 km/h speed, demand, fleet and shift data are estimates, labelled `# ESTIMATE` in every CSV and in the README. The algorithms are correct and the pipeline runs unchanged on measured data; the absolute minute figures are only as good as those assumptions, but the relative improvement from the algorithms is the result.

**16. What are the limitations?** No dwell time, no traffic, straight-line distance at constant speed, estimated demand, static (not time-of-day) demand, and the shuttle slices are contiguous segments of the tour rather than a full vehicle-routing optimisation.

**17. What would you do next?** Survey real roads and ride times, measure boardings, add dwell time, make demand time-dependent, and try a proper VRP heuristic.

**18. (Group project) What was your own contribution?** Every member can be asked this individually. Agree your split before the review (for example: graph and data, MST and shortest paths, scheduling and DP, TSP and wait model, dashboard and report) and make sure each person can explain at least one algorithm end to end, plus the 20-second pitch.

## Quick complexity table
| Algorithm | Time | Space |
|---|---|---|
| Prim | O(E log V) | O(V+E) |
| Kruskal | O(E log E) | O(V+E) |
| Dijkstra | O((V+E) log V) | O(V) |
| Bellman-Ford | O(VE) | O(V) |
| Floyd-Warshall | O(V^3) | O(V^2) |
| Greedy interval scheduling | O(S log S) | O(S) |
| 0-1 knapsack | O(nW) | O(nW) |
| Held-Karp | O(n^2 2^n) | O(n 2^n) |
| Nearest neighbour | O(n^2) | O(n) |
| MST preorder tour | O(V log V) | O(V) |

## Before the review: your checklist
- As a team, agree who presents which slides and who answers which algorithm questions.
- Finish the MOOC and save the certificate PDF.
- Screenshot your LeetCode and HackerRank profiles.
- Run `python main.py` once on your laptop so the dashboard is fresh.
- Open the deck, press F for fullscreen, and test it offline.
- Charge your laptop and keep the deck and `report/dashboard.html` on a pen drive too.
