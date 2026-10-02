# Campus Shuttle Routing & Capacity Scheduling (DAA project)

Run: `pip install -r requirements.txt && python main.py` (outputs go to `report/`).

## Data status: ESTIMATES
- `data/stops.csv`: 14 stops with real names and coordinates (user-provided).
- `data/edges.csv`: **ESTIMATED edge set** (which stops connect is assumed, not surveyed roads); time = haversine distance at an **assumed 20 km/h** shuttle speed, no dwell.
- `data/fleet.csv`, `data/demand.csv`, `data/shifts.csv`: **ESTIMATED** placeholders (Main Gate and Bus Stop are the depots; shuttle speed and demand are assumed).

The estimated data files start with a `# ESTIMATE` comment line (`stops.csv` has none, as its coordinates are real); the loader skips `#` lines. Replace with measured data when available.
