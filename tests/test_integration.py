#!/usr/bin/env python3
"""
Test the multi-sport integration without running the LED matrix.
Shows what would be displayed and in what order.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.config import Config
from data import Data
import debug

# Enable debug logging
debug.set_debug_status(True)

print("=" * 70)
print("Multi-Sport Integration Test")
print("=" * 70)

# Load test configuration
config = Config("config.json.multisport_test")

print(f"\n✓ Config loaded")
print(f"  Multi-sport enabled: {config.multi_sport_enabled}")
print(f"  Sports: {config.multi_sport_sports}")
print(f"  Favorite teams: {config.multi_sport_favorite_teams}")

# Initialize data
print(f"\n⏳ Initializing data...")
data = Data(config)

print(f"\n✓ Data initialized")
print(f"  MLB games today: {data.schedule.num_games()}")
print(f"  Other sport games: {len(data.other_sport_games)}")

# Show MLB games
if data.schedule.num_games() > 0:
    print(f"\n⚾ MLB Games:")
    for i, game in enumerate(data.schedule.games[:5], 1):
        try:
            away = game.away_team_name if hasattr(game, 'away_team_name') else "Unknown"
            home = game.home_team_name if hasattr(game, 'home_team_name') else "Unknown"
            print(f"  {i}. {away} @ {home}")
        except Exception as e:
            print(f"  {i}. Error getting game info: {e}")

# Show other sport games
if data.other_sport_games:
    print(f"\n🏀 NBA Games:")
    for i, game in enumerate(data.other_sport_games[:10], 1):
        status_icon = "🔴" if game.is_live() else ("✓" if game.is_final() else "⏰")
        print(f"  {i}. {status_icon} {game.away_team} @ {game.home_team}")
        if game.is_live() or game.is_final():
            print(f"      Score: {game.away_score}-{game.home_score} {game.get_period_label()}")

# Test game rotation
print(f"\n🔄 Testing Game Rotation:")
print(f"  Current game is other sport: {data.current_game_is_other_sport}")
if data.current_game_is_other_sport and data.current_other_sport_game:
    print(f"  Current: {data.current_other_sport_game.away_team} @ {data.current_other_sport_game.home_team}")
elif data.current_game:
    try:
        print(f"  Current: MLB game {data.current_game.game_id}")
    except:
        print(f"  Current: MLB game (unknown)")
else:
    print(f"  Current: No game selected")

# Simulate rotation
print(f"\n  Rotating through first 5 games...")
for i in range(5):
    data.advance_to_next_game()
    if data.current_game_is_other_sport and data.current_other_sport_game:
        game = data.current_other_sport_game
        print(f"    {i+1}. 🏀 {game.sport.value}: {game.away_team} @ {game.home_team}")
    elif data.current_game:
        try:
            print(f"    {i+1}. ⚾ MLB: {data.current_game.away_team_name} @ {data.current_game.home_team_name}")
        except:
            print(f"    {i+1}. ⚾ MLB: Game {data.current_game.game_id if data.current_game else 'None'}")

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("=" * 70)
print("\nTo use multi-sport on your Pi:")
print("  1. Edit your config.json and set multi_sport.enabled = true")
print("  2. Add your favorite NBA teams with their IDs")
print("  3. Restart the scoreboard: sudo systemctl restart mlb-led-scoreboard")
print("\n")
