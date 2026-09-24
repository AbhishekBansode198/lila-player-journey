"""
Data loader for LILA BLACK player journey data.

Reads all .nakama-0 parquet files, decodes events, detects humans vs bots,
and maps world (x, z) coordinates to minimap pixels.

Public API:
    load_all_data(cache=True) -> pd.DataFrame
    load_matches() -> pd.DataFrame
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

# ---------- CONFIG ----------
DATA_ROOT = Path("data/player_data")
MINIMAP_DIR = DATA_ROOT / "minimaps"
CACHE_PATH = Path("data/cache/all_events.parquet")

MAP_CONFIG = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473, "img": "AmbroseValley_Minimap.png"},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290, "img": "GrandRift_Minimap.png"},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500, "img": "Lockdown_Minimap.jpg"},
}

MINIMAP_SIZE = 1024

# UUID regex — humans have UUID-shaped user_ids
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

# Event classification
MOVEMENT_EVENTS = {"Position", "BotPosition"}
HUMAN_KILL_EVENTS = {"Kill", "BotKill"}       # events where a human got a kill
HUMAN_DEATH_EVENTS = {"Killed", "BotKilled", "KilledByStorm"}  # events where a human died
BOT_DEATH_EVENTS = {"Killed", "BotKilled"}   # we'll refine later
LOOT_EVENTS = {"Loot"}
STORM_EVENTS = {"KilledByStorm"}


# ---------- HELPERS ----------
def _decode_event(x) -> str:
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    return str(x)


def _is_human(user_id: str) -> bool:
    return bool(UUID_RE.match(str(user_id)))


def _world_to_pixel(x: float, z: float, map_id: str) -> tuple[float, float]:
    cfg = MAP_CONFIG.get(map_id)
    if cfg is None:
        return (float("nan"), float("nan"))
    u = (x - cfg["origin_x"]) / cfg["scale"]
    v = (z - cfg["origin_z"]) / cfg["scale"]
    return (u * MINIMAP_SIZE, (1 - v) * MINIMAP_SIZE)


def _read_one(path: Path) -> Optional[pd.DataFrame]:
    try:
        df = pq.read_table(path).to_pandas()
    except Exception as e:
        print(f"[warn] Failed to read {path}: {e}")
        return None
    if df.empty:
        return None
    df["event"] = df["event"].apply(_decode_event)
    df["source_file"] = path.name
    return df


# ---------- MAIN LOADER ----------
def _load_fresh(progress_cb=None) -> pd.DataFrame:
    """Walk all date folders, read all parquet files, return one DataFrame."""
    date_dirs = sorted([d for d in DATA_ROOT.iterdir() if d.is_dir() and d.name.startswith("February") or d.name.startswith("March")])
    all_files: list[Path] = []
    for dd in date_dirs:
        all_files.extend(sorted(dd.glob("*.nakama-0")))

    total = len(all_files)
    print(f"[loader] Found {total} files across {len(date_dirs)} date folders")

    frames = []
    for i, fp in enumerate(all_files, 1):
        df = _read_one(fp)
        if df is not None:
            frames.append(df)
        if progress_cb and (i % 50 == 0 or i == total):
            progress_cb(i, total)

    if not frames:
        raise RuntimeError("No data loaded!")

    big = pd.concat(frames, ignore_index=True)
    print(f"[loader] Combined rows: {len(big):,}")

    # Enrich
    big["is_human"] = big["user_id"].apply(_is_human)
    big["date"] = big["source_file"].apply(lambda _: None)  # placeholder, filled below
    # Extract date from source_file path — we lost path in name only, so instead do it now:
    # (Recompute from stored name pattern)
    # Actually simpler: attach date during file walk — do it inline instead.

    # Derive date folder from filename is impossible; we need path. Let's redo quickly:
    # Alternative: infer from source_file's parent. We didn't keep parent. Fix below.
    return big


# ---------- CLEANER LOADER (keeps date) ----------
def _load_fresh_v2(progress_cb=None) -> pd.DataFrame:
    date_dirs = sorted(
        [d for d in DATA_ROOT.iterdir()
         if d.is_dir() and (d.name.startswith("February") or d.name.startswith("March"))]
    )
    all_files: list[tuple[str, Path]] = []
    for dd in date_dirs:
        for fp in sorted(dd.glob("*.nakama-0")):
            all_files.append((dd.name, fp))

    total = len(all_files)
    print(f"[loader] Found {total} files in {len(date_dirs)} folders")

    frames = []
    for i, (date_name, fp) in enumerate(all_files, 1):
        df = _read_one(fp)
        if df is None:
            continue
        df["date"] = date_name
        frames.append(df)
        if progress_cb and (i % 100 == 0 or i == total):
            progress_cb(i, total)

    if not frames:
        raise RuntimeError("No data loaded")

    big = pd.concat(frames, ignore_index=True)
    print(f"[loader] Total rows: {len(big):,}")

    # Human vs bot
    big["is_human"] = big["user_id"].apply(_is_human)

    # Strip .nakama-0 suffix from match_id for cleaner filtering
    big["match_id_clean"] = big["match_id"].str.replace(r"\.nakama-0$", "", regex=True)

    # Map to pixels
    pix = big.apply(lambda r: _world_to_pixel(r["x"], r["z"], r["map_id"]), axis=1)
    big["px"] = [p[0] for p in pix]
    big["py"] = [p[1] for p in pix]

    # Timestamp in seconds (within match)
    big["t_sec"] = (big["ts"] - big["ts"].min()).dt.total_seconds()

    return big


def load_all_data(use_cache: bool = True, progress_cb=None) -> pd.DataFrame:
    """Load all events. Uses disk cache unless use_cache=False."""
    if use_cache and CACHE_PATH.exists():
        print(f"[loader] Loading from cache: {CACHE_PATH}")
        return pd.read_parquet(CACHE_PATH)

    df = _load_fresh_v2(progress_cb=progress_cb)

    if use_cache:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(CACHE_PATH, index=False)
        print(f"[loader] Cached to {CACHE_PATH}")

    return df


# ---------- HIGH-LEVEL HELPERS ----------
def get_available_maps(df: pd.DataFrame) -> list[str]:
    return sorted(df["map_id"].dropna().unique().tolist())


def get_available_dates(df: pd.DataFrame) -> list[str]:
    return sorted(df["date"].dropna().unique().tolist())


def get_matches_for(df: pd.DataFrame, map_id: str, date: str) -> list[str]:
    sub = df[(df["map_id"] == map_id) & (df["date"] == date)]
    return sorted(sub["match_id_clean"].dropna().unique().tolist())


if __name__ == "__main__":
    # Quick smoke test
    df = load_all_data(use_cache=False)
    print("\n=== LOADED ===")
    print(df.shape)
    print(df.dtypes)
    print("\nHumans:", df["is_human"].sum(), "rows")
    print("Bots:  ", (~df["is_human"]).sum(), "rows")
    print("\nMaps:", get_available_maps(df))
    print("Dates:", get_available_dates(df))
    print("\nEvent counts:")
    print(df["event"].value_counts())