# 🎮 LILA Player Journey Visualizer

An interactive web tool for Level Designers to explore player behavior on LILA BLACK maps — visualizing player paths, combat events, loot pickups, and movement heatmaps from 5 days of production telemetry data.

## 🔗 Live Demo

**https://lila-player-journey-3cb9rbe4rc8nprmnh2tt8n.streamlit.app/**

> Hosted on Streamlit Community Cloud (free tier). If the app is sleeping after inactivity, just click the link — it auto-wakes in ~30-60 seconds.

## ✨ Features

- **Match Playback** — scrub a match timeline to watch players move in real-time
- **Player Paths** — humans (cyan solid) vs. bots (red dotted)
- **Event Markers** — kills, deaths, loot, storm deaths as distinct icons
- **Heatmaps** — kill zones, death zones, or movement traffic per map+date
- **Multi-map** — AmbroseValley, GrandRift, Lockdown
- **Filters** — by map, date, and match
- **Responsive** — works on desktop, tablet, mobile

## 🛠 Tech Stack

| Layer | Tool |
|-------|------|
| Data Processing | Pandas + PyArrow |
| Visualization | Plotly |
| Web UI | Streamlit |
| Hosting | Streamlit Community Cloud |
| Image Handling | Pillow |

## 📦 Local Setup

```bash
git clone https://github.com/AbhishekBansode198/lila-player-journey.git
cd lila-player-journey

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
streamlit run app.py