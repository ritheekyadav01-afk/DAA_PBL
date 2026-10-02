"""Route visualization with networkx layout + plotly."""
import os

import networkx as nx
import plotly.graph_objects as go

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")


def to_networkx(g):
    """Convert to a networkx graph. Time: O(V + E)."""
    G = nx.Graph()
    for v in g.adj:
        G.add_node(v, name=g.names.get(v, v))
    for u, v, w in g.edges():
        G.add_edge(u, v, w=w)
    return G


def _positions(g):
    """lng/lat if available, else spring layout. Time: O(V) or O(iter * V^2)."""
    if all(v in g.coords for v in g.adj):
        return {v: (g.coords[v][1], g.coords[v][0]) for v in g.adj}
    return nx.spring_layout(to_networkx(g), seed=1)


def _edge_trace(pos, edges, color, width, name, dash=None):
    # Time: O(len(edges))
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", name=name,
                      line=dict(color=color, width=width, dash=dash), hoverinfo="skip")


def build_figure(g, mst_edges=None, path=None):
    """Campus map: all roads (gray), MST (blue), shortest route (orange), stops with
    hover names. Time: O(V + E)."""
    pos = _positions(g)
    fig = go.Figure()
    fig.add_trace(_edge_trace(pos, [(u, v) for u, v, _ in g.edges()], "#b5b4ad", 1.5, "Roads"))
    if mst_edges:
        fig.add_trace(_edge_trace(pos, [(u, v) for u, v, _ in mst_edges], "#2a78d6", 3, "MST (Prim/Kruskal)"))
    if path and len(path) > 1:
        fig.add_trace(_edge_trace(pos, list(zip(path, path[1:])), "#eb6834", 5,
                                  f"Shortest route {path[0]} to {path[-1]}"))
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in g.adj], y=[pos[v][1] for v in g.adj], mode="markers+text",
        text=list(g.adj), textposition="top center", name="Stops",
        hovertext=[f"{v}: {g.names.get(v, v)}" for v in g.adj], hoverinfo="text",
        marker=dict(size=11, color="#0b0b0b", line=dict(width=2, color="#fcfcfb"))))
    fig.update_layout(title="Campus shuttle network (placeholder estimates)", template="plotly_white",
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
                      legend=dict(orientation="h", y=-0.05))
    return fig


def save(fig, path=None):
    """Write standalone HTML. Time: O(size of figure)."""
    path = path or os.path.join(REPORT_DIR, "dashboard.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.write_html(path)
    return path
