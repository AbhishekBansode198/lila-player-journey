"""
LILA Player Journey Visualizer — Streamlit app.

Run: streamlit run app.py
"""
import gc
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd

from src.data_loader import (
    load_all_data,
    get_available_maps,
    get_available_dates,
    get_matches_for,
)
from src.visualizations import (
    plot_match_journey,
    plot_heatmap,
    get_match_time_range,
    EVENT_STYLE,
)

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="LILA Player Journey",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="auto",
)

# ---------- CUSTOM CSS (responsive) ----------
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #ffffff; }
    .stat-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3d 100%);
        border-radius: 10px;
        padding: 12px;
        border-left: 4px solid #00E5FF;
        margin-bottom: 8px;
    }
    .stat-label { color: #8892a6; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { color: #ffffff; font-size: 22px; font-weight: bold; margin-top: 4px; }

    /* Make Plotly fill container */
    .js-plotly-plot, .plotly { width: 100% !important; }

    /* Compact on mobile */
    @media (max-width: 768px) {
        .stat-value { font-size: 18px; }
        .stat-label { font-size: 10px; }
        h1 { font-size: 22px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------- DATA LOADING ----------
@st.cache_data(show_spinner="Loading LILA data (first load ~30s)...")
def get_data():
    return load_all_data()

df = get_data()

# ---------- HEADER ----------
st.title("🎮 LILA Player Journey Visualizer")
st.caption("Explore player behavior on LILA BLACK maps — for Level Designers")

# ---------- SIDEBAR FILTERS ----------
st.sidebar.header("🎯 Filters")

maps = get_available_maps(df)
map_choice = st.sidebar.selectbox("Map", maps, index=0)

dates = get_available_dates(df)
date_choice = st.sidebar.selectbox("Date", dates, index=len(dates)-1)

matches = get_matches_for(df, map_choice, date_choice)
if not matches:
    st.sidebar.error("No matches for this filter combo.")
    st.stop()

match_labels = {m: f"Match {m[:8]}…" for m in matches}
match_choice = st.sidebar.selectbox(
    "Match",
    options=matches,
    format_func=lambda m: match_labels[m],
)

# ---------- FILTER DATA ----------
match_df = df[df["match_id_clean"] == match_choice].copy()

if match_df.empty:
    st.warning("No data for this match.")
    st.stop()

# ---------- VIEW MODE ----------
st.sidebar.markdown("---")
st.sidebar.header("👁️ View Settings")

view_mode = st.sidebar.radio(
    "View Mode",
    ["🎬 Match Playback", "🔥 Heatmap"],
    index=0,
)

show_humans = st.sidebar.checkbox("Show Humans", value=True)
show_bots = st.sidebar.checkbox("Show Bots", value=True)
show_events = st.sidebar.checkbox("Show Event Markers", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Clear Cache & Reload"):
    st.cache_data.clear()
    gc.collect()
    st.rerun()

# ---------- MAIN LAYOUT ----------
col_main, col_side = st.columns([3, 1], gap="medium")

with col_main:
    if view_mode == "🎬 Match Playback":
        # Timeline slider
        t_min, t_max = get_match_time_range(match_df)
        if t_max > 0:
            up_to_time = st.slider(
                "⏱️ Match Timeline (seconds)",
                min_value=0.0,
                max_value=float(t_max),
                value=float(t_max),
                step=max(1.0, t_max / 100),
                help="Drag to replay the match from the start",
                key=f"slider_{match_choice}",
            )
        else:
            up_to_time = None

        with st.spinner("Rendering match journey…"):
            fig = plot_match_journey(
                match_df,
                map_choice,
                up_to_time=up_to_time,
                show_humans=show_humans,
                show_bots=show_bots,
                show_events=show_events,
                title=f"{map_choice} · Match {match_choice[:8]}…",
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"journey_{map_choice}_{date_choice}_{match_choice}_{up_to_time if up_to_time is not None else 0}",
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "displaylogo": False,
                    "responsive": True,
                },
            )
            del fig
            gc.collect()

    else:  # Heatmap mode
        heatmap_kind = st.radio(
            "Heatmap Type",
            ["traffic", "kills", "deaths"],
            horizontal=True,
            format_func=lambda x: {
                "traffic": "🚶 Traffic",
                "kills": "⚔️ Kills",
                "deaths": "💀 Deaths",
            }[x],
            key=f"heatkind_{map_choice}_{date_choice}",
        )

        # Use whole map+date for heatmaps (aggregate across matches)
        agg_df = df[(df["map_id"] == map_choice) & (df["date"] == date_choice)]

        with st.spinner("Rendering heatmap…"):
            fig = plot_heatmap(
                agg_df,
                map_choice,
                kind=heatmap_kind,
                title=f"{heatmap_kind.title()} Heatmap · {map_choice} · {date_choice}",
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"heat_{map_choice}_{date_choice}_{heatmap_kind}",
                config={
                    "displayModeBar": True,
                    "scrollZoom": True,
                    "displaylogo": False,
                    "responsive": True,
                },
            )
            del fig
            gc.collect()

# ---------- SIDE STATS PANEL ----------
with col_side:
    st.markdown("### 📊 Match Stats")

    n_players = match_df["user_id"].nunique()
    n_humans = match_df[match_df["is_human"]]["user_id"].nunique()
    n_bots = n_players - n_humans
    duration = match_df["t_sec"].max() if not match_df.empty else 0

    kills = match_df[match_df["event"].isin(["Kill", "BotKill"])].shape[0]
    deaths = match_df[match_df["event"].isin(["Killed", "BotKilled", "KilledByStorm"])].shape[0]
    loot = match_df[match_df["event"] == "Loot"].shape[0]
    storm = match_df[match_df["event"] == "KilledByStorm"].shape[0]

    def card(label, value):
        st.markdown(
            f'<div class="stat-card"><div class="stat-label">{label}</div>'
            f'<div class="stat-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

    card("Duration", f"{duration:.0f}s")
    card("Total Players", n_players)
    card("Humans", n_humans)
    card("Bots", n_bots)
    card("Kills", kills)
    card("Deaths", deaths)
    card("Loot Pickups", loot)
    card("Storm Deaths", storm)

    st.markdown("---")
    with st.expander("🗺️ Legend", expanded=False):
        st.markdown("- 🟦 **Human path** (solid cyan)")
        st.markdown("- 🔴 **Bot path** (dotted red)")
        st.markdown("---")
        for evt, style in EVENT_STYLE.items():
            st.markdown(
                f"<span style='color:{style['color']};font-weight:bold'>"
                f"{style['symbol']} {style['label']}</span>",
                unsafe_allow_html=True,
            )

# ---------- FOOTER ----------
st.markdown("---")
st.caption(
    f"Dataset: {len(df):,} events · {df['match_id_clean'].nunique()} matches · "
    f"{df['user_id'].nunique()} players · {len(maps)} maps"
)