"""Graph (adjacency list) + heapq-based priority queue and CSV loading."""
import csv
import heapq
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def read_csv(path):
    """Read a CSV, skipping '#' comment lines (used for ESTIMATE markers).
    Time: O(R) for R rows."""
    with open(path, newline="") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    return list(csv.DictReader(lines))


class MinHeap:
    """Priority queue over heapq with lazy deletion semantics left to the caller."""

    def __init__(self):
        # Time: O(1)
        self._h = []

    def push(self, priority, item):
        # Time: O(log n)
        heapq.heappush(self._h, (priority, item))

    def pop(self):
        # Time: O(log n)
        return heapq.heappop(self._h)

    def __len__(self):
        # Time: O(1)
        return len(self._h)


class Graph:
    """Undirected weighted graph stored as adjacency list: {u: [(v, w), ...]}."""

    def __init__(self):
        # Time: O(1)
        self.adj = {}
        self.names = {}
        self.coords = {}

    def add_vertex(self, v, name=None, lat=None, lng=None):
        # Time: O(1)
        self.adj.setdefault(v, [])
        if name is not None:
            self.names[v] = name
        if lat is not None:
            self.coords[v] = (lat, lng)

    def add_edge(self, u, v, w, directed=False):
        # Time: O(1)
        self.add_vertex(u)
        self.add_vertex(v)
        self.adj[u].append((v, w))
        if not directed:
            self.adj[v].append((u, w))

    def vertices(self):
        # Time: O(V)
        return list(self.adj)

    def edges(self):
        """Unique undirected edges (u, v, w) with u < v. Time: O(V + E)."""
        out = []
        for u, nbrs in self.adj.items():
            for v, w in nbrs:
                if u < v:
                    out.append((u, v, w))
        return out

    def num_vertices(self):
        # Time: O(1)
        return len(self.adj)

    def num_edges(self):
        # Time: O(V + E)
        return len(self.edges())

    @classmethod
    def from_csv(cls, stops_path=None, edges_path=None):
        """Load graph from stops.csv and edges.csv. Time: O(V + E)."""
        stops_path = stops_path or os.path.join(DATA_DIR, "stops.csv")
        edges_path = edges_path or os.path.join(DATA_DIR, "edges.csv")
        g = cls()
        for r in read_csv(stops_path):
            g.add_vertex(r["stop_id"], r["name"], float(r["lat"]), float(r["lng"]))
        for r in read_csv(edges_path):
            g.add_edge(r["from_stop"], r["to_stop"], float(r["travel_time_min"]))
        return g
