import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_loader import load_all_data, get_matches_for
import src.visualizations

df = load_all_data()
print("Loaded:", df.shape)

# Pick a match on AmbroseValley
matches = get_matches_for(df, "AmbroseValley", "February_14")
print(f"Found {len(matches)} matches. First: {matches[0]}")

# Filter to that match
match_df = df[df["match_id_clean"] == matches[0]]
print(f"Match has {len(match_df)} rows, {match_df['user_id'].nunique()} players")

# Build journey fig
fig = src.visualizations.plot_match_journey(match_df, "AmbroseValley")
fig.write_html("test_journey.html")
print("✅ Wrote test_journey.html — open it in your browser")

# Build kill heatmap for whole map
all_map_df = df[df["map_id"] == "AmbroseValley"]
fig2 = src.visualizations.plot_heatmap(all_map_df, "AmbroseValley", kind="kills")
fig2.write_html("test_kills_heatmap.html")
print("✅ Wrote test_kills_heatmap.html — open it in your browser")