#!/usr/bin/env python3
"""
Test ESPN API provider for NBA.
"""

import sys
sys.path.insert(0, '.')

from datetime import date
from data.models.base_game import Sport
from data.providers.espn_provider import ESPNProvider


def test_espn_nba():
    """Test the ESPN NBA provider."""
    print("=" * 70)
    print("Testing ESPN API - NBA Provider")
    print("=" * 70)
    
    # Initialize provider (no API key needed!)
    print("\n✅ Initializing ESPN NBA Provider (no auth required)...")
    provider = ESPNProvider(sport=Sport.NBA)
    
    # Search for teams
    print("\n--- Team Search ---")
    for team_name in ["Bucks", "Celtics", "Lakers"]:
        teams = provider.search_teams(team_name)
        for team in teams:
            print(f"  {team['name']:30} ID: {team['id']:5} ({team['abbreviation']})")
    
    # Get today's games
    print(f"\n--- Today's NBA Games ({date.today()}) ---")
    games = provider.get_games_for_date(date.today())
    
    if games:
        print(f"\n🏀 Found {len(games)} game(s):\n")
        for i, game in enumerate(games, 1):
            print(f"Game {i}:")
            print(f"  {game.away_team} @ {game.home_team}")
            print(f"  Score: {game.away_score} - {game.home_score}")
            print(f"  Status: {game.status.value}")
            print(f"  Period: {game.get_period_label()}")
            
            if game.get_time_remaining():
                print(f"  Time: {game.get_time_remaining()}")
            
            if game.is_live():
                print(f"  🔴 LIVE GAME!")
            
            print(f"  Venue: {game.venue}")
            print(f"  IDs: Home={game.home_team_id}, Away={game.away_team_id}")
            print()
    else:
        print("  No games today")
    
    # Filter by favorite teams (Bucks, Celtics, Lakers)
    print("\n--- Filtering by Favorite Teams ---")
    favorite_team_ids = ["15", "2", "13"]  # Bucks, Celtics, Lakers (ESPN IDs)
    print(f"Favorites: Bucks (15), Celtics (2), Lakers (13)")
    
    filtered_games = provider.get_games_for_date(date.today(), team_ids=favorite_team_ids)
    
    if filtered_games:
        print(f"\n⭐ Found {len(filtered_games)} game(s) with favorite teams:\n")
        for game in filtered_games:
            print(f"  {game.away_team} @ {game.home_team}")
            print(f"  Status: {game.status.value} - {game.get_period_label()}")
    else:
        print("  No favorite teams playing today")
    
    print("\n" + "=" * 70)
    print("ESPN API Summary")
    print("=" * 70)
    print("""
✅ ESPN API Benefits:
  • FREE - No API key required
  • LIVE SCORES - Real-time updates
  • CLEAN DATA - Well-structured JSON
  • ALL SPORTS - NBA, NHL, NFL, MLB, Soccer
  • RELIABLE - Powers ESPN.com

Ready to integrate into scoreboard!
    """)
    print("=" * 70)


if __name__ == "__main__":
    test_espn_nba()
