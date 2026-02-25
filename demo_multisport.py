#!/usr/bin/env python3
"""
Demo of multi-sport integration.
Shows how MLB and NBA games will appear together.
"""

import requests
from datetime import date

print("=" * 70)
print("Multi-Sport Scoreboard Demo")
print("=" * 70)

# Configure favorites
mlb_teams = ["New York Yankees"]
nba_teams = ["Milwaukee Bucks (15)", "Boston Celtics (2)"]

print("\n📋 Configured Favorite Teams:")
print(f"  ⚾ MLB: {', '.join(mlb_teams)}")
print(f"  🏀 NBA: {', '.join(nba_teams)}")

# Get MLB games (using ESPN for demo, normally would use statsapi)
print(f"\n📅 Fetching games for {date.today()}...")

mlb_url = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
mlb_response = requests.get(mlb_url, params={"dates": date.today().strftime("%Y%m%d")})
mlb_data = mlb_response.json()
mlb_games = mlb_data.get("events", [])

nba_url = "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
nba_response = requests.get(nba_url, params={"dates": date.today().strftime("%Y%m%d")})
nba_data = nba_response.json()
nba_games = nba_data.get("events", [])

# Combine and prioritize
all_games = []

print(f"\n⚾ MLB Games: {len(mlb_games)}")
for event in mlb_games[:3]:
    comp = event.get("competitions", [{}])[0]
    status = comp.get("status", {}).get("type", {}).get("state", "pre")
    all_games.append({
        "sport": "MLB",
        "name": event.get("name"),
        "status": status,
        "priority": 0 if status == "in" else (1 if status == "pre" else 2)
    })
    print(f"  {event.get('name')}")

print(f"\n🏀 NBA Games: {len(nba_games)}")
for event in nba_games[:3]:
    comp = event.get("competitions", [{}])[0]
    status = comp.get("status", {}).get("type", {}).get("state", "pre")
    
    # Check if it's a favorite team
    competitors = comp.get("competitors", [])
    team_ids = [str(c.get("team", {}).get("id")) for c in competitors]
    is_favorite = "15" in team_ids or "2" in team_ids  # Bucks or Celtics
    
    marker = "⭐" if is_favorite else "  "
    
    all_games.append({
        "sport": "NBA",
        "name": event.get("name"),
        "status": status,
        "priority": 0 if status == "in" else (1 if status == "pre" else 2),
        "favorite": is_favorite
    })
    print(f"  {marker}{event.get('name')}")

# Sort by priority (live first)
all_games.sort(key=lambda g: g["priority"])

print("\n" + "=" * 70)
print("Scoreboard Display Order (Live games first)")
print("=" * 70)

for i, game in enumerate(all_games[:10], 1):
    sport_icon = "⚾" if game["sport"] == "MLB" else "🏀"
    status_icon = "🔴" if game["priority"] == 0 else ("⏰" if game["priority"] == 1 else "✓")
    fav_marker = " ⭐" if game.get("favorite") else ""
    
    print(f"{i}. {sport_icon} {status_icon} {game['name']}{fav_marker}")

print("\n" + "=" * 70)
print("How It Works")
print("=" * 70)
print("""
The scoreboard will cycle through games in this order:

1. 🔴 LIVE games (any sport) - Priority 1
2. ⏰ SCHEDULED games - Priority 2  
3. ✓ FINAL games - Priority 3

Each game displays for ~15 seconds before rotating.

Configuration (config.json):
  "multi_sport": {
    "enabled": true,
    "sports": ["MLB", "NBA"],
    "favorite_teams": {
      "NBA": [
        {"name": "Milwaukee Bucks", "id": "15"},
        {"name": "Boston Celtics", "id": "2"}
      ]
    }
  }

To enable: Set "enabled": true in your config.json!
""")
print("=" * 70)
