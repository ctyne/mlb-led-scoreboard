#!/usr/bin/env python3
"""Debug script to show raw ESPN soccer API data."""

import requests
import json
from datetime import date

# Wrexham team ID from config.example.json
WREXHAM_ID = "352"

# ESPN soccer leagues to check
SOCCER_LEAGUES = [
    "soccer/eng.1",  # Premier League
    "soccer/eng.2",  # Championship
    "soccer/eng.3",  # League One
    "soccer/eng.4",  # League Two
]

print("Fetching ESPN soccer data for Wrexham...")
print("=" * 70)

for league_path in SOCCER_LEAGUES:
    url = f"http://site.api.espn.com/apis/site/v2/sports/{league_path}/scoreboard"
    params = {"dates": date.today().strftime("%Y%m%d")}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        events = data.get("events", [])
        
        for event in events:
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            
            # Check if Wrexham is playing
            team_ids = [str(c.get("team", {}).get("id", "")) for c in competitors]
            
            if WREXHAM_ID in team_ids:
                print(f"\nFound Wrexham game in {league_path}")
                print("=" * 70)
                
                # Get status info
                status_data = competition.get("status", {})
                status_type = status_data.get("type", {})
                
                print("\nSTATUS INFO:")
                print(f"  state: {status_type.get('state')}")
                print(f"  detail: {status_type.get('detail')}")
                print(f"  period: {status_type.get('period')}")
                print(f"  displayClock: {status_data.get('displayClock')}")
                
                print("\nFULL STATUS DATA:")
                print(json.dumps(status_data, indent=2))
                
                print("\nFULL EVENT DATA:")
                print(json.dumps(event, indent=2))
                
    except Exception as e:
        print(f"Error checking {league_path}: {e}")

print("\n" + "=" * 70)
