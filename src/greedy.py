"""Greedy activity selection for driver shifts."""
import os
from src.graph import DATA_DIR, read_csv


def _mins(hhmm):
    # Time: O(1)
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def load_shifts(path=None):
    """Load shifts as (id, start_min, end_min). Time: O(S)."""
    path = path or os.path.join(DATA_DIR, "shifts.csv")
    return [(r["shift_id"], _mins(r["start"]), _mins(r["end"])) for r in read_csv(path)]


def select_shifts(shifts):
    """Classic earliest-finish-time-first: max number of non-overlapping shifts
    one driver can cover. Optimal by exchange argument.
    Time: O(S log S) (sort) + O(S) scan."""
    chosen, last_end = [], -1
    for s in sorted(shifts, key=lambda s: s[2]):
        if s[1] >= last_end:
            chosen.append(s)
            last_end = s[2]
    return chosen


def assign_drivers(shifts):
    """Cover ALL shifts with the fewest drivers by repeatedly running activity
    selection on the remaining shifts (greedy; interval-partitioning style).
    Time: O(D * S log S) for D drivers (D <= S, so O(S^2 log S) worst case)."""
    remaining, drivers = list(shifts), []
    while remaining:
        pick = select_shifts(remaining)
        drivers.append(pick)
        ids = {s[0] for s in pick}
        remaining = [s for s in remaining if s[0] not in ids]
    return drivers
