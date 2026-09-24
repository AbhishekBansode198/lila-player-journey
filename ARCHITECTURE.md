# Architecture - LILA Player Journey Visualizer

## Tech Stack & Rationale

| Layer | Choice | Why |
|-------|--------|-----|
| Data Processing | Pandas + PyArrow | Native Parquet support, vectorized ops, 89K rows |
| Visualization | Plotly | Interactive zoom/pan, heatmaps, image overlays |
| Web UI | Streamlit | Fastest path from data to filterable app |
| Hosting | Streamlit Community Cloud | One-click GitHub deploy, free shareable URL |
| Image Handling | Pillow | Minimap loading, RGB conversion, downsampling |

**Why Streamlit over React?** Level Designers need to explore data quickly, not click a bespoke frontend. Streamlit maps directly to "change filter -> see result" without a separate API layer.

## Data Flow
1243 .nakama-0 Parquet files (5 date folders, 3 maps)
|
v
data_loader.py

Read parquet via PyArrow

Decode event bytes -> string

Detect humans vs bots (UUID vs numeric user_id)

Map (x, z) world -> (px, py) pixel

Attach date folder

Cache to data/cache/all_events.parquet
|
v
visualizations.py

Load minimap (cached, 384px downsampled)

Add image as Plotly layer

Draw batched paths (1 trace for humans, 1 for bots)

Add event markers (1 trace per event type)

Add heatmap (Histogram2dContour, sampled to 5K pts)
|
v
app.py (Streamlit UI)

Sidebar: map, date, match, view mode, filters

Timeline slider for playback

Plotly chart with responsive config

Stats panel (players, kills, deaths, loot, storm)

## Coordinate Mapping - The Tricky Part

### The Challenge
The game uses world coordinates `(x, z)` in 3D space. The minimap is a 2D image (1024x1024). We need a deterministic transform.

### The Formula (from `data/player_data/README.md`)
u = (x - origin_x) / scale
v = (z - origin_z) / scale
pixel_x = u * 1024
pixel_y = (1 - v) * 1024 <- Y flipped (image origin top-left)

### Map Config
| Map | Scale | Origin X | Origin Z |
|-----|-------|----------|----------|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

### Verification
README example: world `(-301.45, -355.55)` -> pixel `(78, 890)`. Our implementation matches **exactly** (see `notebooks/verify_data.py`). Zero out-of-bounds rows across all 89,104 events.

### Critical Details
- Use `x` and `z`, NOT `y` (y is elevation).
- Flip Y-axis (image origin is top-left, world origin is bottom-left).
- Downsample image to 384px (1024px caused browser OOM; 384 is visually indistinguishable).

## Assumptions Made

| Ambiguity | Assumption | Impact |
|-----------|-----------|--------|
| Bot detection | user_id format (UUID = human, numeric = bot) | Used README as source of truth |
| `ts` column | Milliseconds since match start (not wall clock) | Relative time used for playback |
| Event bytes | `event` stored as bytes in parquet | Decoded with `.decode('utf-8')` |
| Match grouping | match_id uniquely IDs a match | Stripped `.nakama-0` suffix for UI |
| Storm events | KilledByStorm = storm deaths | 39 events total; distinct marker |

## Major Tradeoffs

| Decision | Alternative | Why We Chose This |
|----------|-------------|-------------------|
| Streamlit | React + FastAPI | 10x faster dev; flexible enough |
| Plotly | D3.js custom | Built-in heatmaps, zoom, legends; no custom JS |
| Batched traces (None-separated) | One trace per player | 50+ traces/match caused browser OOM; batching -> 8 traces |
| 384px minimap | 1024px original | 7x smaller payload; visual difference imperceptible |
| Disk cache (data/cache/) | Reload every launch | First load ~30s, cached loads <1s |
| Client-side slider | Server-side playback | No backend; slider filters traces in browser |
| Sample heatmap to 5K pts | Plot all points | Rare-event heatmaps can have 10K+ points |

## Performance

- Initial load: ~30s (parsing 1,243 parquet files)
- Subsequent loads: <1s (from disk cache)
- Chart render: 1-3s per match
- Heatmap render: <2s (5K point cap)

## File Structure
lila-player-journey/
|-- app.py # Streamlit UI
|-- requirements.txt
|-- .streamlit/config.toml # Dark theme + message size limit
|-- src/
| |-- init.py
| |-- data_loader.py # Load, decode, cache, coordinate mapping
| -- visualizations.py # Plotly figure builders |-- data/ | |-- player_data/ # Raw telemetry (committed) |-- cache/ # Regenerable cache (gitignored)
|-- notebooks/
| |-- verify_data.py # Data sanity checks
| -- test_viz.py # Figure smoke tests |-- ARCHITECTURE.md-- INSIGHTS.md


## Component Responsibilities

- **`app.py`** - Streamlit UI, sidebar filters, stats panel, chart rendering
- **`src/data_loader.py`** - Parquet reading, event decoding, human/bot detection, coordinate mapping, disk cache
- **`src/visualizations.py`** - Plotly figures: minimap, paths, events, heatmaps, responsive layout

Keeping visualization logic separate from the Streamlit UI makes the code easier to test and maintain.