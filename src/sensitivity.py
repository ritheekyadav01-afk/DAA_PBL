"""Average passenger wait vs fleet size, using slices of the MST tour."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.apsp import floyd_warshall
from src.dp import load_demand
from src.wait_model import mst_tour, split_even, stop_weights, weighted_wait

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report")


def run(g, mst_edges, start, kmax=6, threshold=0.5):
    """Wait for k = 1..kmax shuttles, each looping one contiguous slice of the
    MST preorder tour. `knee` is the first k whose extra shuttle saves less than
    `threshold` min (None if never). Time: O(V^3) Floyd-Warshall + O(kmax * V)."""
    d, _ = floyd_warshall(g)
    w = stop_weights(load_demand())
    tour = mst_tour(mst_edges, d, start)
    ks = list(range(1, min(kmax, len(tour)) + 1))
    waits = [weighted_wait(split_even(tour, k), d, w) for k in ks]
    gains = [None] + [waits[i - 1] - waits[i] for i in range(1, len(waits))]
    knee = next((k for k, gain in zip(ks, gains) if gain is not None and gain < threshold), None)
    return {"k": ks, "wait": waits, "gain": gains, "knee": knee, "threshold": threshold}


def plot(res, path=None):
    """Line chart of wait vs fleet size. Time: O(kmax)."""
    path = path or os.path.join(REPORT_DIR, "fleet_sensitivity.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(res["k"], res["wait"], "o-", color="#2a78d6")
    for k, wt in zip(res["k"], res["wait"]):
        ax.annotate(f"{wt:.2f}", (k, wt), textcoords="offset points", xytext=(0, 8), ha="center")
    if res["knee"]:
        ax.axvline(res["knee"], color="#eb6834", ls="--",
                   label=f"gain < {res['threshold']} min from {res['knee']} shuttles")
        ax.legend()
    ax.set_xlabel("number of shuttles")
    ax.set_ylabel("average passenger wait (min)")
    ax.set_title("Wait vs fleet size (MST tour slices; estimated inputs)")
    ax.set_xticks(res["k"])
    ax.set_ylim(0, max(res["wait"]) * 1.2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path
