# Campus Shuttle Routing & Capacity Scheduling

**Design and Analysis of Algorithms (DAA) group project, Woxsen University, B.Tech AI & ML**

| Name | Student ID |
|---|---|
| D. Ritheek | 25WU0102057 |
| M. Srilakshmi | 25WU0102140 |
| B. Deekshan | 25WU0102037 |
| P. Priyakaran | 25WU0101090 |
| G. Madhan | 25WU0102344 |

## 1. What this project does

A campus shuttle is only useful if passengers do not wait long. We model 14 Woxsen campus stops as a weighted graph and apply the classical algorithm families from the course to design a better shuttle service:

| Question | Algorithm(s) | Result on our data |
|---|---|---|
| Cheapest set of roads connecting all stops | Prim, Kruskal | 5.81 min total (both agree) |
| Fastest route between two stops | Dijkstra, Bellman-Ford | Bus Stop to Race Arena: 3.3 min |
| Fastest route between every pair | Floyd-Warshall | Longest shortest trip: 4.3 min (Main Gate to Cricket Ground) |
| Fewest drivers for the shifts | Greedy earliest-finish-time | 1 driver covers 8 of 18 shifts; 4 drivers cover all |
| Which passenger groups go on which vehicle | 0-1 knapsack DP | BUS-1 30/30 seats, BUS-2 19/20, VAN-1 9/12 |
| Best closed tour of all stops | Held-Karp (exact), nearest neighbour, MST 2-approximation | file order 13.37, NN 10.11, MST 10.11, optimal 9.92 min |
| Passenger waiting time | Wait model (loop time / 2, demand weighted) | **6.69 min to 2.03 min (70% lower)** |

Headline result: with one shuttle visiting stops in file order, average wait is 6.69 min. Three shuttles running contiguous slices of the MST-based tour bring it to 2.03 min. The MST tour is within 1.019x of the exact optimum (theory only guarantees 2x).

## 2. IMPORTANT: what is real data and what is estimated

- `data/stops.csv`: **real** stop names and GPS coordinates.
- `data/edges.csv`, `data/demand.csv`, `data/fleet.csv`, `data/shifts.csv`: **estimates**. Which stops connect, the 20 km/h speed, passenger demand, fleet and shifts were not surveyed. Each file starts with a `# ESTIMATE` line (the loader skips `#` lines).

The algorithms are correct and run unchanged on measured data; absolute minute values are only as good as these assumptions, while the relative gains are the finding.

## 3. Quick start

```bash
git clone https://github.com/ritheekyadav01-afk/DAA_PBL.git
cd DAA_PBL
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py        # runs every algorithm, prints results, writes report/
pytest -q             # 202 tests
```

`main.py` prints all results and regenerates `report/dashboard.html` (open in any browser, no server needed) and the charts in `report/`.

## 4. Repository layout

```
main.py                 entry point: runs the whole pipeline
data/                   stops.csv (real), edges/demand/fleet/shifts.csv (estimates)
src/
  graph.py              adjacency-list graph, min-heap, CSV loader
  mst.py                Prim and Kruskal (union-find)
  sssp.py               Dijkstra and Bellman-Ford (negative-cycle detection)
  apsp.py               Floyd-Warshall with path reconstruction
  greedy.py             earliest-finish interval scheduling, driver assignment
  dp.py                 0-1 knapsack with item reconstruction
  tsp.py                tour cost, nearest neighbour, MST preorder, Held-Karp
  wait_model.py         average wait, shuttle slicing
  sensitivity.py        wait vs fleet size
  experiments.py        random graphs, runtime benchmarks
  dashboard.py          interactive Plotly dashboard
tests/test_algorithms.py  202 tests (cross-checks and brute force)
report/                 dashboard.html and generated charts
docs/                   project report (docx and pdf)
final_review/           review deck (html, pdf), presentation script, viva prep
```

## 5. The algorithms

| Algorithm | Time | Space | Used for |
|---|---|---|---|
| Prim (binary heap) | O(E log V) | O(V+E) | MST |
| Kruskal (union-find) | O(E log E) | O(V+E) | MST (cross-check) |
| Dijkstra | O((V+E) log V) | O(V) | shortest routes |
| Bellman-Ford | O(VE) | O(V) | cross-check, negative cycles |
| Floyd-Warshall | O(V^3) | O(V^2) | all-pairs distance matrix |
| Greedy interval scheduling | O(S log S) | O(S) | shifts and drivers |
| 0-1 knapsack | O(nW) | O(nW) | vehicle loading |
| Held-Karp | O(n^2 2^n) | O(n 2^n) | exact tour (n = 14) |
| Nearest neighbour | O(n^2) | O(n) | heuristic tour |
| MST preorder tour | O(V log V) | O(V) | 2-approximation tour |

**Graph model.** Stops are vertices; roads are undirected edges weighted by haversine distance divided by 20 km/h, in minutes.

**Wait model.** For a loop of T minutes and uniform arrivals, the average wait at a stop is T/2, weighted by the passengers starting at each stop. Baseline: one shuttle, stops in file order. After: three shuttles, each running a contiguous slice of the MST tour, which shortens every loop.

## 6. Results

| Configuration | Avg wait (min) |
|---|---|
| One shuttle, file order (baseline) | 6.69 |
| One shuttle, MST tour | 5.05 |
| Three shuttles, MST tour slices | **2.03** |

Fleet sensitivity (avg wait): 1 shuttle 5.05, 2: 3.91, 3: 2.03, 4: 1.75, 5: 1.26, 6: 1.12. Three shuttles is the knee of the curve. Charts: `report/fleet_sensitivity.png`, `report/runtime_vs_complexity.png`.

## 7. Verification

202 automated tests, mostly independent cross-checks: Prim vs Kruskal, Dijkstra vs Bellman-Ford vs Floyd-Warshall, Held-Karp vs brute-force permutations, knapsack vs brute-force subsets, and Held-Karp never losing to the heuristics, over many random seeds. A runtime benchmark (50 to 1600 nodes) confirms the expected growth.

## 8. Documents

- `docs/DAA_Project_Report.docx` / `.pdf`: first-draft project report (problem, literature survey, SRS, design, algorithms, results, testing, limitations).
- `final_review/DAA_Campus_Shuttle_Deck.pptx` / `.pdf` / `.html`: final review deck.
- `notebooks/walkthrough.ipynb`: Jupyter notebook that runs the pipeline, shows the charts and runs the tests.
- `final_review/DAA_Presentation_Script.pdf`: speaking script.
- `final_review/DAA_Viva_Prep.md`: likely viva questions and answers.

## 9. Limitations

Straight-line distances at constant speed, no dwell time or traffic, estimated demand and road set, static demand, contiguous-slice shuttles rather than a full vehicle-routing optimisation, greedy driver assignment is a heuristic. Future work: survey real roads and boardings, add dwell time and time-of-day demand, try a proper VRP heuristic.

## 10. References

Cormen et al., *Introduction to Algorithms*; Kruskal (1956); Prim (1957); Dijkstra (1959); Bellman (1958); Floyd (1962); Held and Karp (1962); Rosenkrantz, Stearns and Lewis (1977). Full list in the report.
