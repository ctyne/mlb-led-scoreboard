#!/usr/bin/env python3
"""
Test script for TheSportsDB NBA provider.
Fetches upcoming NBA games and displays them.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
import requests


def test_nba_api():
    """Test the NBA API with upcoming games."""
    print("=" * 60)
    print("Testing TheSportsDB NBA API")
    print("=" * 60)
    
    api_key = "123"  # User's API key with NBA access
    league_id = "4387"  # NBA
    
    # Get next 15 upcoming games
    print("\n--- Upcoming NBA Games ---")
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsnextleague.php"
    response = requests.get(url, params={"id": league_id})
    data = response.json()
    
    events = data.get("events", [])
    if events:
        print(f"Found {len(events)} upcoming NBA games:\n")
        
        # Show next 5 games
        for i, event in enumerate(events[:5], 1):
            print(f"Game {i}:")
            print(f"  {event['strAwayTeam']} @ {event['strHomeTeam']}")
            print(f"  Date: {event['dateEvent']} at {event.get('strTime', 'TBD')}")
            print(f"  Status: {event.get('strStatus', 'Scheduled')}")
            print(f"  Venue: {event.get('strVenue', 'N/A')}")
            
            # Show team IDs (useful for configuration)
            print(f"  Team IDs: Home={event['idHomeTeam']}, Away={event['idAwayTeam']}")
            print()
        
        # Test getting details for the first game
        if events:
            print("\n--- Testing Game Details ---")
            first_game_id = events[0]['idEvent']
            print(f"Fetching details for game ID: {first_game_id}")
            
            url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/lookupevent.php"
            response = requests.get(url, params={"id": first_game_id})
            game_data = response.json()
            
            if game_data.get("events"):
                game = game_data["events"][0]
                print(f"\n  Full Details:")
                print(f"    Event: {game['strEvent']}")
                print(f"    League: {game['strLeague']}")
                print(f"    Season: {game['strSeason']}")
                print(f"    Round: {game.get('intRound', 'N/A')}")
                print(f"    Location: {game.get('strCity', 'N/A')}, {game.get('strCountry', 'N/A')}")
    else:
        print("No upcoming NBA games found")
    
    # Test team search for configuration
    print("\n--- Popular NBA Teams (for configuration) ---")
    print("Search results for popular teams:\n")
    
    for team_name in ["Lakers", "Celtics", "Warriors", "Heat"]:
        url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/searchteams.php"
        response = requests.get(url, params={"t": team_name})
        data = response.json()
        
        teams = data.get("teams") or []
        for team in teams:
            if str(team.get("idLeague")) == league_id:
                print(f"  {team['strTeam']:25} (ID: {team['idTeam']}) - {team.get('strStadium', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("\nTo track these teams, add their IDs to your config:")
    print('  "favorite_teams": [')
    print('    {"sport": "NBA", "team_id": "134880", "name": "Atlanta Hawks"},')
    print('    ...')
    print('  ]')
    print("=" * 60)


if __name__ == "__main__":
    test_nba_api()
