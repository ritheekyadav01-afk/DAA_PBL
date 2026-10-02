"""Route visualization with networkx layout + plotly."""
import json
import os

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.sssp import dijkstra, reconstruct_path

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")
TITLE = "Campus Shuttle Network (estimated distances)"
ROUTE_TRACE = 3  # index of the selectable route trace in the figure


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


def _edge_trace(pos, edges, color, width, name):
    # Time: O(len(edges))
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", name=name,
                      line=dict(color=color, width=width), hoverinfo="skip")


def all_routes(g):
    """Shortest route for every ordered stop pair via Dijkstra from each source.
    Time: O(V (V + E) log V)."""
    routes = {}
    for s in g.adj:
        dist, prev = dijkstra(g, s)
        routes[s] = {t: {"path": reconstruct_path(prev, s, t), "min": dist[t]} for t in g.adj}
    return routes


def build_figure(g, mst_edges, wait, src, dst):
    """Row 1: campus map (named stops, edge-time hover, MST, selectable route).
    Row 2: average-wait bar chart. Time: O(V + E)."""
    pos = _positions(g)
    nm = lambda v: g.names.get(v, v)
    fig = make_subplots(rows=2, cols=1, row_heights=[0.68, 0.32], vertical_spacing=0.12,
                        subplot_titles=("", "Average passenger wait: before vs after"))
    fig.add_trace(_edge_trace(pos, [(u, v) for u, v, _ in g.edges()], "#b5b4ad", 1.5, "Roads"), 1, 1)
    edges = g.edges()
    fig.add_trace(go.Scatter(  # invisible midpoints so hovering an edge shows its time
        x=[(pos[u][0] + pos[v][0]) / 2 for u, v, _ in edges],
        y=[(pos[u][1] + pos[v][1]) / 2 for u, v, _ in edges],
        mode="markers", name="Road times", showlegend=False,
        marker=dict(size=14, color="rgba(0,0,0,0)"),
        hovertext=[f"{nm(u)} ↔ {nm(v)}: {w:.1f} min" for u, v, w in edges], hoverinfo="text"), 1, 1)
    fig.add_trace(_edge_trace(pos, [(u, v) for u, v, _ in mst_edges], "#2a78d6", 3, "MST (Prim/Kruskal)"), 1, 1)
    routes = all_routes(g)
    r = routes[src][dst]
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in r["path"]], y=[pos[v][1] for v in r["path"]], mode="lines",
        name=f"Shortest route: {nm(src)} to {nm(dst)} ({r['min']:.1f} min)",
        line=dict(color="#eb6834", width=5), hoverinfo="skip"), 1, 1)
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in g.adj], y=[pos[v][1] for v in g.adj], mode="markers+text",
        text=[nm(v) for v in g.adj], textposition="top center", name="Stops",
        hovertext=[f"{v}: {nm(v)}" for v in g.adj], hoverinfo="text",
        marker=dict(size=11, color="#0b0b0b", line=dict(width=2, color="#fcfcfb"))), 1, 1)

    labels = ["Before<br>(naive, 1 shuttle)", "Route only<br>(MST tour, 1 shuttle)",
              f"After<br>(MST tour, {wait['k']} shuttles)"]
    vals = [wait["before"], wait["route_only"], wait["after"]]
    fig.add_trace(go.Bar(
        x=labels, y=vals, marker_color=["#2a78d6", "#eb6834", "#1baf7a"], showlegend=False,
        text=[f"{v:.1f} min" for v in vals], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{y:.2f} min<extra></extra>"), 2, 1)
    fig.update_yaxes(title_text="avg wait (min)", range=[0, max(vals) * 1.35], row=2, col=1)
    fig.add_annotation(
        x=labels[2], y=max(vals) * 1.22, xref="x2", yref="y2", showarrow=False,
        text=f"<b>{wait['improvement_pct']:.0f}% shorter wait</b> than baseline",
        font=dict(size=14))
    fig.add_annotation(
        x=0, y=-0.17, xref="paper", yref="paper", xanchor="left", yanchor="top", showarrow=False,
        align="left", font=dict(size=11),
        text="<b>Baseline assumptions (all inputs are estimates):</b><br>"
             + "<br>".join("• " + a for a in wait["assumptions"]))
    fig.update_layout(title=TITLE, template="plotly_white", height=1150, margin=dict(t=120, b=240),
                      legend=dict(orientation="h", y=1.0, yanchor="bottom"))
    fig.update_xaxes(visible=False, row=1, col=1)
    ys = [p[1] for p in pos.values()]
    pad = (max(ys) - min(ys)) * 0.1
    fig.update_yaxes(visible=False, scaleanchor="x", range=[min(ys) - pad, max(ys) + pad], row=1, col=1)

    data = {"names": {v: nm(v) for v in g.adj}, "pos": {v: list(pos[v]) for v in g.adj},
            "routes": routes, "src": src, "dst": dst}
    return fig, data


_JS = """
var gd = document.getElementById('{plot_id}');
var D = %s;
var bar = document.createElement('div');
bar.style.cssText = 'font:14px sans-serif;margin:8px 16px';
function sel(id, val) {
  var s = '<select id="' + id + '">';
  Object.keys(D.names).forEach(function (k) {
    s += '<option value="' + k + '"' + (k === val ? ' selected' : '') + '>' + D.names[k] + '</option>';
  });
  return s + '</select>';
}
bar.innerHTML = 'Route from ' + sel('rs', D.src) + ' to ' + sel('rt', D.dst) +
  ' <span id="rinfo" style="margin-left:12px"></span>';
gd.parentNode.insertBefore(bar, gd);
function update() {
  var s = document.getElementById('rs').value, t = document.getElementById('rt').value;
  var r = D.routes[s][t];
  var xs = r.path.map(function (v) { return D.pos[v][0]; });
  var ys = r.path.map(function (v) { return D.pos[v][1]; });
  var label = 'Shortest route: ' + D.names[s] + ' to ' + D.names[t] + ' (' + r.min.toFixed(1) + ' min)';
  Plotly.restyle(gd, {x: [xs], y: [ys], name: [label]}, [%d]);
  document.getElementById('rinfo').textContent =
    r.path.map(function (v) { return D.names[v]; }).join(' \\u2192 ') + ' \\u2014 ' + r.min.toFixed(1) + ' min';
}
document.getElementById('rs').onchange = update;
document.getElementById('rt').onchange = update;
update();
"""


def save(fig, data, path=None):
    """Write standalone HTML with the route dropdowns. Time: O(size of figure + V^2 routes)."""
    path = path or os.path.join(REPORT_DIR, "dashboard.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.write_html(path, post_script=_JS % (json.dumps(data), ROUTE_TRACE))
    return path
