"""
TheSportsDB API provider for NBA, NHL, NFL, and Soccer.
"""

import requests
from typing import List, Optional, Dict
from datetime import date, datetime
from data.models.base_game import BaseGame, GameStatus, Sport
from data.models.nba_game import NBAGame
from data.providers.base_provider import BaseProvider


class TheSportsDBProvider(BaseProvider):
    """
    Provider for TheSportsDB API.
    Supports NBA, NHL, NFL, and Soccer leagues.
    """
    
    BASE_URL = "https://www.thesportsdb.com/api/v1/json"
    
    # League IDs for supported sports
    LEAGUE_IDS = {
        Sport.NBA: "4387",
        Sport.NHL: "4380",
        Sport.NFL: "4391",
        Sport.MLB: "4424",
        Sport.SOCCER: "4328"  # English Premier League (can support others)
    }
    
    def __init__(self, sport: Sport, api_key: str = "123"):
        """
        Initialize TheSportsDB provider for a specific sport.
        
        Args:
            sport: The sport this provider will fetch (NBA, NHL, NFL, SOCCER)
            api_key: TheSportsDB API key (default "123" for better access than free tier)
        """
        super().__init__(api_key)
        self._sport = sport
        self.league_id = self.LEAGUE_IDS.get(sport)
        
        if not self.league_id:
            raise ValueError(f"Sport {sport} not supported by TheSportsDB provider")
    
    def get_sport(self) -> Sport:
        """Return the sport this provider handles."""
        return self._sport
    
    def get_games_for_date(self, game_date: date, team_ids: Optional[List[str]] = None) -> List[BaseGame]:
        """
        Fetch NBA games for a specific date.
        
        Args:
            game_date: The date to fetch games for
            team_ids: Optional list of team IDs to filter by
            
        Returns:
            List of NBAGame objects
        """
        # TheSportsDB uses different endpoints for different date ranges
        # For today's games, we can use eventsnextleague
        # For specific dates, we need to search events by date
        
        date_str = game_date.strftime("%Y-%m-%d")
        
        # Try to get events for this league around this date
        url = f"{self.BASE_URL}/{self.api_key}/eventsday.php"
        params = {
            "d": date_str,
            "l": self.league_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            if not events:
                return []
            
            games = []
            for event in events:
                # Filter by team IDs if specified
                if team_ids:
                    home_id = str(event.get("idHomeTeam", ""))
                    away_id = str(event.get("idAwayTeam", ""))
                    if home_id not in team_ids and away_id not in team_ids:
                        continue
                
                game = self._parse_event_to_game(event)
                if game:
                    games.append(game)
            
            return games
            
        except Exception as e:
            print(f"Error fetching games from TheSportsDB: {e}")
            return []
    
    def get_game_details(self, game_id: str) -> Optional[BaseGame]:
        """
        Fetch detailed information for a specific game.
        
        Args:
            game_id: The TheSportsDB event ID
            
        Returns:
            NBAGame object with full details
        """
        url = f"{self.BASE_URL}/{self.api_key}/lookupevent.php"
        params = {"id": game_id}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            if events:
                return self._parse_event_to_game(events[0])
            
            return None
            
        except Exception as e:
            print(f"Error fetching game {game_id}: {e}")
            return None
    
    def search_teams(self, query: str) -> List[Dict[str, str]]:
        """
        Search for teams by name.
        
        Args:
            query: Team name search query
            
        Returns:
            List of team dictionaries
        """
        url = f"{self.BASE_URL}/{self.api_key}/searchteams.php"
        params = {"t": query}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            teams = data.get("teams", [])
            if not teams:
                return []
            
            results = []
            for team in teams:
                # Only return teams from our sport/league
                if str(team.get("idLeague")) == self.league_id:
                    results.append({
                        "id": str(team.get("idTeam", "")),
                        "name": team.get("strTeam", ""),
                        "abbreviation": team.get("strTeamShort", ""),
                        "alternate": team.get("strAlternate", "")
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching teams: {e}")
            return []
    
    def _parse_event_to_game(self, event: dict) -> Optional[BaseGame]:
        """Parse TheSportsDB event JSON to a game model."""
        if self._sport == Sport.NBA:
            return self._parse_nba_event(event)
        # TODO: Add parsers for other sports
        return None
    
    def _parse_nba_event(self, event: dict) -> Optional[NBAGame]:
        """Parse NBA event from TheSportsDB."""
        game = NBAGame()
        
        # Basic info
        game.game_id = str(event.get("idEvent", ""))
        game.home_team = event.get("strHomeTeam", "")
        game.away_team = event.get("strAwayTeam", "")
        game.home_team_id = str(event.get("idHomeTeam", ""))
        game.away_team_id = str(event.get("idAwayTeam", ""))
        
        # Scores
        game.home_score = int(event.get("intHomeScore") or 0)
        game.away_score = int(event.get("intAwayScore") or 0)
        
        # Status
        status_str = event.get("strStatus", "").lower()
        if status_str == "not started":
            game.status = GameStatus.SCHEDULED
        elif status_str in ["1st quarter", "2nd quarter", "3rd quarter", "4th quarter", "halftime", "overtime"]:
            game.status = GameStatus.LIVE
        elif status_str == "final" or status_str == "ft":
            game.status = GameStatus.FINAL
        elif status_str == "postponed":
            game.status = GameStatus.POSTPONED
        elif status_str == "cancelled":
            game.status = GameStatus.CANCELLED
        
        # Parse quarter from status
        if "1st quarter" in status_str:
            game.quarter = 1
        elif "2nd quarter" in status_str:
            game.quarter = 2
        elif "3rd quarter" in status_str:
            game.quarter = 3
        elif "4th quarter" in status_str:
            game.quarter = 4
        elif "overtime" in status_str:
            game.quarter = 5
            game.is_overtime = True
        
        # Timing
        game.game_date = event.get("dateEvent")
        timestamp = event.get("strTimestamp")
        if timestamp:
            try:
                game.start_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                pass
        
        # Venue
        game.venue = event.get("strVenue")
        game.league = event.get("strLeague")
        game.season = event.get("strSeason")
        
        return game
