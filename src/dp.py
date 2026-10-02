"""0-1 knapsack for passenger-group-to-shuttle assignment."""
import os
from src.graph import DATA_DIR, read_csv


def load_fleet(path=None):
    """Time: O(F)."""
    path = path or os.path.join(DATA_DIR, "fleet.csv")
    return [(r["shuttle_id"], int(r["capacity"])) for r in read_csv(path)]


def load_demand(path=None):
    """Groups as dicts with int passengers/priority. Time: O(G)."""
    path = path or os.path.join(DATA_DIR, "demand.csv")
    rows = read_csv(path)
    for r in rows:
        r["passengers"] = int(r["passengers"])
        r["priority"] = int(r["priority"])
    return rows


def knapsack(weights, values, capacity):
    """0-1 knapsack, bottom-up table with item reconstruction.
    Returns (best_value, chosen_indices). Time: O(n * W). Space: O(n * W)."""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1)
            c -= weights[i - 1]
    return dp[n][capacity], chosen[::-1]


def assign_groups(groups, fleet):
    """Fill shuttles one by one (largest first); each is a knapsack where
    weight = passengers and value = passengers * priority. Groups are never split.
    Time: O(F * G * W_max). Returns (assignment, unassigned_groups)."""
    remaining = list(groups)
    assignment = {}
    for sid, cap in sorted(fleet, key=lambda f: -f[1]):
        best, idx = knapsack([g["passengers"] for g in remaining],
                             [g["passengers"] * g["priority"] for g in remaining], cap)
        assignment[sid] = {"capacity": cap, "value": best, "groups": [remaining[i] for i in idx]}
        picked = set(idx)
        remaining = [g for i, g in enumerate(remaining) if i not in picked]
    return assignment, remaining
