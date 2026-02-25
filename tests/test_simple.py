#!/usr/bin/env python3
"""
Simple test that doesn't require all MLB scoreboard dependencies.
Just tests the multi-sport data fetching.
"""

import sys
import os
from datetime import date

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Multi-Sport Data Fetching Test")
print("=" * 70)

# Import directly to avoid data/__init__.py dependencies
from data.models.nba_game import NBAGame
from data.models.base_game import Sport, GameStatus
from data.providers.espn_provider import ESPNProvider

# Test NBA provider
print("\n🏀 Testing NBA Provider...")
nba_provider = ESPNProvider(Sport.NBA)

# Get today's games
print(f"📅 Fetching NBA games for {date.today()}...")
nba_games = nba_provider.get_todays_games()

print(f"\n✅ Found {len(nba_games)} NBA games")

for i, game in enumerate(nba_games, 1):
    status_icon = "🔴" if game.is_live() else ("✓" if game.is_final() else "⏰")
    print(f"\n{i}. {status_icon} {game.away_team} @ {game.home_team}")
    print(f"   Status: {game.status.value}")
    
    if game.is_live() or game.is_final():
        print(f"   Score: {game.away_score} - {game.home_score}")
        print(f"   Period: {game.get_period_label()}")
        if game.time_remaining:
            print(f"   Time: {game.time_remaining}")
    
    if game.game_time_local:
        print(f"   Start: {game.game_time_local}")

# Test filtering by favorite teams
print(f"\n\n⭐ Testing Favorite Team Filtering...")
favorite_ids = ["15", "2"]  # Bucks, Celtics
print(f"   Favorites: Milwaukee Bucks (15), Boston Celtics (2)")

favorite_games = nba_provider.get_games_for_teams(favorite_ids, date.today())
print(f"\n✅ Found {len(favorite_games)} games for favorite teams")

for i, game in enumerate(favorite_games, 1):
    status_icon = "🔴" if game.is_live() else ("✓" if game.is_final() else "⏰")
    print(f"\n{i}. {status_icon} {game.away_team} @ {game.home_team}")
    print(f"   Status: {game.status.value}")
    if game.is_live() or game.is_final():
        print(f"   Score: {game.away_score} - {game.home_score} {game.get_period_label()}")

print("\n" + "=" * 70)
print("✅ Multi-Sport Provider Test Complete!")
print("=" * 70)
