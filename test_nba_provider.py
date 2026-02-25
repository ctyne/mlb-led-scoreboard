#!/usr/bin/env python3
"""
Test script for TheSportsDB NBA provider.
Fetches today's NBA games and displays them.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
import requests


def test_nba_api():
    """Test the NBA API directly."""
    print("=" * 60)
    print("Testing TheSportsDB NBA API")
    print("=" * 60)
    
    api_key = "3"  # Free tier
    league_id = "4387"  # NBA
    
    # Test team search
    print("\n--- Testing Team Search ---")
    print("Searching for 'Celtics'...")
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/searchteams.php"
    response = requests.get(url, params={"t": "Celtics"})
    data = response.json()
    
    teams = data.get("teams", [])
    if teams:
        for team in teams:
            if str(team.get("idLeague")) == league_id:
                print(f"  Found: {team['strTeam']} (ID: {team['idTeam']})")
    
    # Get today's games
    print("\n--- Testing Today's NBA Games ---")
    today = date.today()
    print(f"Fetching games for {today}...")
    
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsday.php"
    response = requests.get(url, params={"d": today.strftime("%Y-%m-%d"), "l": league_id})
    data = response.json()
    
    events = data.get("events", [])
    if events:
        print(f"\n  Found {len(events)} game(s):\n")
        for i, event in enumerate(events, 1):
            print(f"  Game {i}:")
            print(f"    {event['strAwayTeam']} @ {event['strHomeTeam']}")
            print(f"    Score: {event.get('intAwayScore', 0)} - {event.get('intHomeScore', 0)}")
            print(f"    Status: {event.get('strStatus', 'Unknown')}")
            print(f"    Time: {event.get('strTime', 'TBD')}")
            print()
    else:
        print("  No games today")
        print("\nTrying to get next 15 events in the league...")
        url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsnextleague.php"
        response = requests.get(url, params={"id": league_id})
        data = response.json()
        events = data.get("events", [])
        if events:
            print(f"  Found {len(events)} upcoming games:")
            for event in events[:5]:  # Show first 5
                print(f"    {event['strEvent']} - {event['dateEvent']}")
        else:
            print("  No upcoming games found")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_nba_api()
