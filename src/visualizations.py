"""
Visualization module for LILA Player Journey tool.

Builds Plotly figures: minimap + paths + events + heatmaps.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

from src.data_loader import MAP_CONFIG, MINIMAP_DIR, MINIMAP_SIZE

# ---------- COLOR & STYLE ----------
HUMAN_COLOR = "#00E5FF"      # cyan
BOT_COLOR   = "#FF6B6B"      # coral red

EVENT_STYLE = {
    "Kill":         {"color": "#FF1744", "symbol": "x",          "size": 14, "label": "Kill (human killed human)"},
    "Killed":       {"color": "#7B1FA2", "symbol": "x-open",     "size": 14, "label": "Killed (human died to human)"},
    "BotKill":      {"color": "#FF9100", "symbol": "star",       "size": 12, "label": "Bot Kill (human killed bot)"},
    "BotKilled":    {"color": "#FFC400", "symbol": "circle-open","size": 12, "label": "Bot Killed (human died to bot)"},
    "KilledByStorm":{"color": "#00B0FF", "symbol": "diamond",    "size": 14, "label": "Killed by Storm"},
    "Loot":         {"color": "#76FF03", "symbol": "circle",     "size": 7,  "label": "Loot"},
}

HUMAN_LINE_WIDTH = 3
BOT_LINE_WIDTH = 1.5


# ---------- RESPONSIVE HELPER ----------
def make_responsive(fig: go.Figure) -> go.Figure:
    """Apply responsive settings to any Plotly figure."""
    fig.update_layout(
        autosize=True,
        height=None,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


# ---------- HELPERS ----------
@lru_cache(maxsize=8)
def _minimap_image(map_id: str) -> np.ndarray:
    """Load minimap PNG/JPG as numpy array for Plotly background.
    Cached + downsampled to 384px to keep payload small."""
    cfg = MAP_CONFIG[map_id]
    img_path = MINIMAP_DIR / cfg["img"]
    with Image.open(img_path) as img:
        img = img.convert("RGB")
        img = img.resize((384, 384), Image.LANCZOS)
        return np.array(img)


def _empty_fig(map_id: str, title: str = "") -> go.Figure:
    """Create a figure with just the minimap as background."""
    img = _minimap_image(map_id)
    fig = go.Figure()
    fig.add_trace(go.Image(
        z=img,
        x0=0, dx=MINIMAP_SIZE / img.shape[1],
        y0=0, dy=MINIMAP_SIZE / img.shape[0],
        hoverinfo="skip",
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(range=[0, MINIMAP_SIZE], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[MINIMAP_SIZE, 0], showgrid=False, zeroline=False, visible=False, scaleanchor="x"),
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="black",
        paper_bgcolor="#0e1117",
        font=dict(color="white"),
        hovermode="closest",
        uirevision=map_id,
        dragmode="pan",
    )
    return make_responsive(fig)


# ---------- MAIN: MATCH JOURNEY (BATCHED) ----------
def plot_match_journey(
    df_match: pd.DataFrame,
    map_id: str,
    up_to_time: float | None = None,
    show_humans: bool = True,
    show_bots: bool = True,
    show_events: bool = True,
    title: str | None = None,
) -> go.Figure:
    """Plot all player paths + events for one match — BATCHED for performance."""
    fig = _empty_fig(map_id, title=title or f"Match on {map_id}")

    if up_to_time is not None:
        df_match = df_match[df_match["t_sec"] <= up_to_time]
    if df_match.empty:
        return fig

    # ---- BATCHED PATHS ----
    for is_human_group, color, dash, label in [
        (True,  HUMAN_COLOR, "solid", "🧑 Humans"),
        (False, BOT_COLOR,   "dot",   "🤖 Bots"),
    ]:
        if is_human_group and not show_humans:
            continue
        if (not is_human_group) and not show_bots:
            continue

        xs, ys = [], []
        sub = df_match[df_match["is_human"] == is_human_group]
        if sub.empty:
            continue

        for uid, g in sub.groupby("user_id"):
            m = g[g["event"].isin(["Position", "BotPosition"])].sort_values("t_sec")
            if m.empty:
                continue
            xs.extend(m["px"].tolist() + [None])
            ys.extend(m["py"].tolist() + [None])

        if not xs:
            continue

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            line=dict(color=color, width=2.5 if is_human_group else 1.5, dash=dash),
            name=label,
            legendgroup="paths",
            hoverinfo="skip",
        ))

    # ---- START MARKERS ----
    starts = (
        df_match[df_match["event"].isin(["Position", "BotPosition"])]
        .sort_values("t_sec")
        .groupby("user_id").first().reset_index()
    )
    if not starts.empty:
        human_starts = starts[starts["is_human"]]
        bot_starts = starts[~starts["is_human"]]
        if not human_starts.empty and show_humans:
            fig.add_trace(go.Scatter(
                x=human_starts["px"], y=human_starts["py"],
                mode="markers",
                marker=dict(color=HUMAN_COLOR, size=9, symbol="circle",
                            line=dict(color="white", width=1)),
                name="Human start",
                legendgroup="paths",
                hovertemplate="Human start<br>%{customdata}<extra></extra>",
                customdata=human_starts["user_id"],
            ))
        if not bot_starts.empty and show_bots:
            fig.add_trace(go.Scatter(
                x=bot_starts["px"], y=bot_starts["py"],
                mode="markers",
                marker=dict(color=BOT_COLOR, size=7, symbol="square",
                            line=dict(color="white", width=1)),
                name="Bot start",
                legendgroup="paths",
                hovertemplate="Bot start<br>%{customdata}<extra></extra>",
                customdata=bot_starts["user_id"],
            ))

    # ---- EVENT MARKERS ----
    if show_events:
        for evt, style in EVENT_STYLE.items():
            sub = df_match[df_match["event"] == evt]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub["px"], y=sub["py"],
                mode="markers",
                marker=dict(
                    color=style["color"], size=style["size"],
                    symbol=style["symbol"],
                    line=dict(color="white", width=0.8),
                ),
                name=f"{style['label']} ({len(sub)})",
                legendgroup="events",
                hovertemplate=(
                    f"<b>{style['label']}</b><br>"
                    "Player: %{customdata[0]}<br>"
                    "t=%{customdata[1]:.0f}s<extra></extra>"
                ),
                customdata=sub[["user_id", "t_sec"]].values,
            ))

    fig.update_layout(
        legend=dict(
            bgcolor="rgba(0,0,0,0.6)",
            bordercolor="white", borderwidth=1,
            font=dict(color="white", size=11),
        )
    )
    return make_responsive(fig)


# ---------- HEATMAPS ----------
def plot_heatmap(
    df_filtered: pd.DataFrame,
    map_id: str,
    kind: str = "traffic",
    title: str | None = None,
) -> go.Figure:
    """Heatmap overlay on minimap."""
    fig = _empty_fig(map_id, title=title or f"{kind.title()} Heatmap — {map_id}")

    if kind == "traffic":
        sub = df_filtered[df_filtered["event"].isin(["Position", "BotPosition"])]
        colorscale = "Viridis"
    elif kind == "kills":
        sub = df_filtered[df_filtered["event"].isin(["Kill", "BotKill"])]
        colorscale = "Hot"
    elif kind == "deaths":
        sub = df_filtered[df_filtered["event"].isin(["Killed", "BotKilled", "KilledByStorm"])]
        colorscale = "Reds"
    else:
        raise ValueError(f"Unknown heatmap kind: {kind}")

    if sub.empty:
        return fig

    # Downsample to keep payload small
    if len(sub) > 5000:
        sub = sub.sample(5000, random_state=42)

    fig.add_trace(go.Histogram2dContour(
        x=sub["px"],
        y=sub["py"],
        colorscale=colorscale,
        opacity=0.55,
        contours=dict(showlines=False),
        ncontours=12,
        showscale=True,
        hovertemplate="pixel: (%{x:.0f}, %{y:.0f})<br>count: %{z}<extra></extra>",
    ))
    fig.update_yaxes(range=[MINIMAP_SIZE, 0])
    return make_responsive(fig)


# ---------- TIMELINE SCRUBBER HELPER ----------
def get_match_time_range(df_match: pd.DataFrame) -> tuple[float, float]:
    if df_match.empty:
        return (0.0, 1.0)
    return (0.0, float(df_match["t_sec"].max()))