#!/usr/bin/env python3
"""
Test multi-sport scheduler with MLB and NBA.
Demonstrates how the scoreboard will cycle through different sports.
"""

import requests
from datetime import date


def test_multisport():
    """Test fetching games from NBA with favorites."""
    print("=" * 70)
    print("Multi-Sport Scoreboard Test - NBA Configuration")
    print("=" * 70)
    
    # Configure favorite NBA teams
    favorite_teams = {
        "Milwaukee Bucks": "134871",
        "Boston Celtics": "134860",
        "Los Angeles Lakers": "134866"
    }
    
    print("\n📋 Configured Favorite NBA Teams:")
    for team, team_id in favorite_teams.items():
        print(f"  • {team} (ID: {team_id})")
    
    # Check today's NBA games
    print(f"\n📅 Checking NBA games for {date.today()}...")
    
    response = requests.get(
        "https://www.thesportsdb.com/api/v1/json/123/eventsday.php",
        params={"d": date.today().strftime("%Y-%m-%d"), "l": "4387"}
    )
    data = response.json()
    events = data.get("events") or []
    
    if events:
        print(f"\n✅ Found {len(events)} NBA game(s) today:\n")
        for i, event in enumerate(events, 1):
            home_id = str(event.get("idHomeTeam"))
            away_id = str(event.get("idAwayTeam"))
            is_favorite = home_id in favorite_teams.values() or away_id in favorite_teams.values()
            
            marker = "⭐" if is_favorite else "  "
            print(f"{marker} Game {i}:")
            print(f"  {event['strAwayTeam']} @ {event['strHomeTeam']}")
            print(f"  Score: {event.get('intAwayScore', 0)} - {event.get('intHomeScore', 0)}")
            print(f"  Status: {event.get('strStatus', 'Unknown')}")
            if is_favorite:
                print(f"  ⭐ FAVORITE TEAM PLAYING")
            print()
    else:
        print("  ℹ️  No NBA games today")
    
    # Check next Bucks game
    print("\n🦌 Next Milwaukee Bucks Game:")
    response = requests.get(
        "https://www.thesportsdb.com/api/v1/json/123/eventsnext.php",
        params={"id": "134871"}  # Bucks ID
    )
    data = response.json()
    events = data.get("events") or []
    
    if events:
        next_game = events[0]
        print(f"  📍 {next_game['strEvent']}")
        print(f"  📅 {next_game['dateEvent']} at {next_game.get('strTime', 'TBD')}")
        print(f"  📊 Status: {next_game.get('strStatus', 'Scheduled')}")
        if next_game.get('intHomeScore') and next_game.get('intAwayScore'):
            print(f"  🏀 Score: {next_game.get('intAwayScore')} - {next_game.get('intHomeScore')}")
    else:
        print("  No upcoming games found")
    
    print("\n" + "=" * 70)
    print("How Multi-Sport Will Work On Your Scoreboard")
    print("=" * 70)
    print("""
The scoreboard will:

1. ⚾ Show MLB games (Yankees, etc.) using statsapi  
2. 🏀 Show NBA games (Bucks, Celtics, Lakers) using TheSportsDB
3. 🏒 Show NHL games (if configured)
4. 🏈 Show NFL games (if configured)
5. ⚽ Show Soccer games (if configured)

Game Priority:
  • LIVE games shown first (any sport)
  • Scheduled games next (by start time)
  • Completed games last

Cycling:
  • If multiple games are live, cycle through them
  • Each game displays for ~10 seconds before switching
  • Sport-specific layouts for each game type

Configuration (config.json):
  {
    "sports": {
      "enabled": ["MLB", "NBA"],
      "favorite_teams": [
        {"sport": "MLB", "team_id": "147", "name": "New York Yankees"},
        {"sport": "NBA", "team_id": "134871", "name": "Milwaukee Bucks"},
        {"sport": "NBA", "team_id": "134860", "name": "Boston Celtics"}
      ]
    }
  }
    """)
    print("=" * 70)


if __name__ == "__main__":
    test_multisport()
