# Campus Shuttle Routing & Capacity Scheduling (DAA project)

Run: `pip install -r requirements.txt && python main.py` (outputs go to `report/`).

## Data status: ESTIMATES
- `data/stops.csv`: the 11 stop names are real. **lat/lng are ESTIMATED relative positions** around an assumed Woxsen origin, only to make the map look like a plausible campus. Not surveyed.
- `data/edges.csv`: **ESTIMATED**. Each stop links to its 2 nearest stops (plus a few bridging edges so the graph is connected); time = straight-line distance x 1.3 at ~15 km/h + 0.5 min dwell.
- `data/fleet.csv`, `data/demand.csv`, `data/shifts.csv`: **ESTIMATED** placeholders (Main Gate and Bus Stop are the depots).

Each file starts with a `# ESTIMATE` comment line; the loader skips `#` lines. Replace with measured data when available.
