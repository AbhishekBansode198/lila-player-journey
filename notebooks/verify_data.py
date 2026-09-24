"""
Step 2 Verification Script
Confirms: parquet reads, events decode, coordinates map correctly.
"""
import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
DATA_ROOT = Path("data/player_data")
BOT_FILE = DATA_ROOT / "February_14" / "1379_14a40253-7313-40c4-a541-4a7be8962984.nakama-0"
HUMAN_FILE = DATA_ROOT / "February_14" / "10648aa3-b215-4c52-9577-5c5689a08939_1be12bb5-454e-4cd1-a305-de20f5be03a3.nakama-0"

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

# ---------- HELPERS ----------
def decode_events(df):
    df = df.copy()
    df['event_str'] = df['event'].apply(
        lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x)
    )
    return df

def world_to_pixel(x, z, map_name):
    cfg = MAP_CONFIG[map_name]
    u = (x - cfg['origin_x']) / cfg['scale']
    v = (z - cfg['origin_z']) / cfg['scale']
    return u * 1024, (1 - v) * 1024

# ---------- 2.1 READ ONE FILE ----------
print("=" * 70)
print("2.1  READING A BOT FILE")
print("=" * 70)
print(f"File: {BOT_FILE}\n")

df = pq.read_table(BOT_FILE).to_pandas()
df = decode_events(df)

print("--- Schema ---")
print(df.dtypes)
print()

print("--- Shape ---")
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
print()

print("--- First 5 Rows ---")
print(df[['user_id', 'match_id', 'map_id', 'x', 'y', 'z', 'ts', 'event_str']].head())
print()

print("--- Event Counts ---")
print(df['event_str'].value_counts())
print()

print("--- Coordinate Ranges ---")
print(f"x: {df['x'].min():.2f}  →  {df['x'].max():.2f}")
print(f"y: {df['y'].min():.2f}  →  {df['y'].max():.2f}  (elevation)")
print(f"z: {df['z'].min():.2f}  →  {df['z'].max():.2f}")
print()

print("--- Timestamp Range ---")
print(f"ts min: {df['ts'].min()}")
print(f"ts max: {df['ts'].max()}")
print()

print("--- Unique IDs ---")
print(f"user_id: {df['user_id'].unique()}")
print(f"match_id: {df['match_id'].unique()}")
print(f"map_id: {df['map_id'].unique()}")
print()

# ---------- 2.2 READ A HUMAN FILE ----------
print("=" * 70)
print("2.2  READING A HUMAN FILE")
print("=" * 70)
print(f"File: {HUMAN_FILE}\n")

hdf = pq.read_table(HUMAN_FILE).to_pandas()
hdf = decode_events(hdf)

print("--- Human File Event Counts ---")
print(hdf['event_str'].value_counts())
print()
print("user_id:", hdf['user_id'].iloc[0])
print("match_id:", hdf['match_id'].iloc[0])
print("map_id:", hdf['map_id'].iloc[0])
print()

# ---------- 2.3 COORDINATE MAPPING ----------
print("=" * 70)
print("2.3  COORDINATE MAPPING VERIFICATION")
print("=" * 70)

# Test with README example
px, py = world_to_pixel(-301.45, -355.55, "AmbroseValley")
print(f"README example: world(-301.45, -355.55) → pixel({px:.0f}, {py:.0f})")
print(f"README expects: pixel(78, 890)")
print(f"Match? {'YES ✅' if abs(px-78) < 2 and abs(py-890) < 2 else 'NO ❌'}")
print()

# Apply to entire bot file
map_name = df['map_id'].iloc[0]
pixels = df.apply(lambda r: world_to_pixel(r['x'], r['z'], map_name), axis=1)
df['px'] = [p[0] for p in pixels]
df['py'] = [p[1] for p in pixels]

print(f"Map: {map_name}")
print(f"pixel_x range: {df['px'].min():.0f} → {df['px'].max():.0f}   (ideal: 0–1024)")
print(f"pixel_y range: {df['py'].min():.0f} → {df['py'].max():.0f}   (ideal: 0–1024)")
print()

oob = df[(df['px'] < 0) | (df['px'] > 1024) | (df['py'] < 0) | (df['py'] > 1024)]
print(f"Out-of-bounds rows: {len(oob)} / {len(df)}")
if len(oob) > 0:
    print("Sample out-of-bounds:")
    print(oob[['x', 'z', 'px', 'py', 'event_str']].head(10))

print()
print("=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)