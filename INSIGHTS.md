# Three Insights from LILA BLACK Telemetry

> Based on 89,104 events across 5 days (Feb 10-14, 2026), 1,243 matches, 3 maps.

---

## Insight 1: Combat is 99.8% PvE — Real PvP is Essentially Absent

### What Caught My Eye
The event breakdown is striking:

| Event | Count |
|-------|-------|
| `BotKill` (human killed bot) | 2,415 |
| `BotKilled` (human died to bot) | 700 |
| `Kill` (human killed human) | 3 |
| `Killed` (human died to human) | 3 |

### The Pattern
Out of ~3,100 total combat outcomes, only **6** are human-vs-human. That's 0.19%.

Either matchmaking rarely puts humans together, humans actively avoid each other, or most matches are effectively PvE.

### Actionable for Level Designers
- **Metrics affected:** Human-vs-human encounter rate, time-to-first-PvP
- **Actions:**
  - Lower bot count in lobbies; measure if PvP rate rises
  - Add high-value loot zones that force human convergence
  - Reduce match duration so players cannot farm safely

### Why They Should Care
If 99.8% of combat is PvE, the game does not yet have a PvP loop — it has a bot-farming loop. Level design should either enable human encounters or embrace PvE intent.

---

## Insight 2: Two Kill Hotspots Dominate AmbroseValley

### What Caught My Eye
The kill heatmap for AmbroseValley shows **two intense clusters**:
1. Center-left cluster — heaviest concentration
2. Bottom-left cluster — secondary

The rest of the map is nearly empty of kills.

### The Pattern
Roughly **60-70% of all kills** on AmbroseValley happen in these two zones. Bot kills cluster here too, suggesting bots follow predictable paths into these zones.

### Actionable for Level Designers
- **Metrics affected:** Kill density per zone, player retention in mid-game
- **Actions:**
  - If intentional -> lean in: make these iconic, high-stakes zones
  - If accidental -> add loot/objectives to under-used regions to spread traffic
  - Consider secondary extract point to pull players elsewhere
  - Add cover or escape routes if the chokepoints are too punishing

### Why They Should Care
A map where everyone fights in the same two spots gets boring after 20 matches. Level designers should either make these iconic or break them up.

---

## Insight 3: Storm Deaths Are Negligible — The Storm Isn't a Threat

### What Caught My Eye
Only **39 storm deaths** across 5 days (~0.04% of all events). Compare to 2,415 bot kills and 700 human deaths to bots.

### The Pattern
The storm kills **~8 players per day** across ~250 matches/day. Statistically irrelevant. Either:
1. Players extract well before the storm closes in,
2. The storm is too slow / too forgiving, or
3. Matches end before the storm becomes lethal.

### Actionable for Level Designers
- **Metrics affected:** Storm death rate, average match duration, extract usage
- **Actions:**
  - Speed up the storm timer by 20-30%; observe if storm deaths rise
  - Add a hard storm event (sudden wall) forcing immediate movement
  - If player-friendly pacing is intended, accept that storm is cosmetic and design combat challenges instead

### Why They Should Care
In extraction shooters, the storm (or circle) is the primary pacing mechanism. If it never kills anyone, it is not pacing anything — it is just a timer. Either fix it or replace it with a different pressure system.

---

## Summary

| # | Insight | Key Stat | Primary Action |
|---|---------|----------|----------------|
| 1 | Combat is 99.8% PvE | 2,415 bot kills vs 3 human kills | Test bot count vs PvP encounter rate |
| 2 | Two kill hotspots dominate | ~65% of AmbroseValley kills in 2 zones | Lean into or break up chokepoints |
| 3 | Storm is harmless | 39 storm deaths in 5 days | Speed up storm or add hard wall event |