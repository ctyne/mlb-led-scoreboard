"""
ESPN API provider for NBA, NCAAB, NHL, NFL, MLB, and Soccer.
Free, no authentication required, includes live scores!
"""

import requests
from typing import List, Optional, Dict
from datetime import date, datetime
from data.models.base_game import BaseGame, GameStatus, Sport
from data.models.nba_game import NBAGame
from data.models.ncaab_game import NCAABGame
from data.models.nhl_game import NHLGame
from data.models.soccer_game import SoccerGame
from data.providers.base_provider import BaseProvider


class ESPNProvider(BaseProvider):
    """
    Provider for ESPN's public API.
    Supports NBA, NCAAB, NHL, NFL, MLB with real-time live scores.
    No authentication required!
    """
    
    BASE_URL = "http://site.api.espn.com/apis/site/v2/sports"
    
    # Sport to ESPN path mapping
    SPORT_PATHS = {
        Sport.NBA: "basketball/nba",
        Sport.NCAAB: "basketball/mens-college-basketball",
        Sport.NHL: "hockey/nhl",
        Sport.NFL: "football/nfl",
        Sport.MLB: "baseball/mlb",
        Sport.SOCCER: "soccer/eng.1"  # Default to Premier League
    }
    
    # Multiple soccer leagues and competitions (will check all for favorite teams)
    # Track teams across all competitions, not just league matches
    SOCCER_LEAGUES = [
        # English Leagues
        "soccer/eng.1",  # Premier League
        "soccer/eng.2",  # Championship (EFL Championship)
        "soccer/eng.3",  # League One
        "soccer/eng.4",  # League Two
        # English Cups
        "soccer/eng.fa",  # FA Cup
        "soccer/eng.league_cup",  # EFL Cup (Carabao Cup)
        # European Competitions
        "soccer/uefa.champions",  # UEFA Champions League
        "soccer/uefa.europa",  # UEFA Europa League
        "soccer/uefa.europa.conf",  # UEFA Europa Conference League
        # North American
        "soccer/usa.1",  # MLS
        # International/Friendlies
        "soccer/fifa.friendly",  # International friendlies
        "soccer/club.friendly"   # Club friendlies
    ]
    
    def __init__(self, sport: Sport):
        """
        Initialize ESPN provider for a specific sport.
        
        Args:
            sport: The sport this provider will fetch (NBA, NHL, NFL, MLB, SOCCER)
        """
        super().__init__(api_key=None)  # No API key needed!
        self._sport = sport
        self.sport_path = self.SPORT_PATHS.get(sport)
        
        if not self.sport_path:
            raise ValueError(f"Sport {sport} not supported by ESPN provider")
    
    def get_sport(self) -> Sport:
        """Return the sport this provider handles."""
        return self._sport
    
    def get_games_for_date(self, game_date: date, team_ids: Optional[List[str]] = None) -> List[BaseGame]:
        """
        Fetch games for a specific date.
        
        Args:
            game_date: The date to fetch games for
            team_ids: Optional list of ESPN team IDs to filter by
            
        Returns:
            List of BaseGame objects
        """
        all_games = []
        
        # For soccer, check multiple leagues
        if self._sport == Sport.SOCCER:
            for league_path in self.SOCCER_LEAGUES:
                url = f"{self.BASE_URL}/{league_path}/scoreboard"
                date_str = game_date.strftime("%Y%m%d")
                params = {"dates": date_str}
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    events = data.get("events", [])
                    
                    for event in events:
                        game = self._parse_event_to_game(event)
                        if game:
                            # Filter by team IDs if provided
                            if team_ids is None or game.home_team_id in team_ids or game.away_team_id in team_ids:
                                all_games.append(game)
                except Exception as e:
                    # Continue to next league if one fails
                    continue
            
            return all_games
        
        # For other sports, use single endpoint
        url = f"{self.BASE_URL}/{self.sport_path}/scoreboard"
        date_str = game_date.strftime("%Y%m%d")
        params = {"dates": date_str}
        
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
                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])
                    
                    event_team_ids = [str(c.get("team", {}).get("id", "")) for c in competitors]
                    
                    # Check if any of the favorite teams are playing
                    if not any(tid in team_ids for tid in event_team_ids):
                        continue
                
                game = self._parse_event_to_game(event)
                if game:
                    games.append(game)
            
            return games
            
        except Exception as e:
            print(f"Error fetching games from ESPN: {e}")
            return []
    
    def get_game_details(self, game_id: str) -> Optional[BaseGame]:
        """
        Fetch detailed information for a specific game.
        
        Args:
            game_id: The ESPN event ID
            
        Returns:
            BaseGame object with full details
        """
        url = f"{self.BASE_URL}/{self.sport_path}/summary"
        params = {"event": game_id}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            header = data.get("header", {})
            event = header.get("competitions", [{}])[0]
            
            # Create a simplified event structure
            simplified_event = {
                "id": game_id,
                "competitions": [event]
            }
            
            return self._parse_event_to_game(simplified_event)
            
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
        url = f"{self.BASE_URL}/{self.sport_path}/teams"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            teams = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
            if not teams:
                return []
            
            results = []
            query_lower = query.lower()
            
            for team_data in teams:
                team = team_data.get("team", {})
                team_name = team.get("displayName", "")
                
                if query_lower in team_name.lower():
                    results.append({
                        "id": str(team.get("id", "")),
                        "name": team_name,
                        "abbreviation": team.get("abbreviation", ""),
                        "location": team.get("location", "")
                    })
            
            return results
            
        except Exception as e:
            print(f"Error searching teams: {e}")
            return []
    
    def _parse_event_to_game(self, event: dict) -> Optional[BaseGame]:
        """Parse ESPN event JSON to a game model."""
        if self._sport == Sport.NBA:
            return self._parse_nba_event(event)
        elif self._sport == Sport.NCAAB:
            return self._parse_ncaab_event(event)
        elif self._sport == Sport.NHL:
            return self._parse_nhl_event(event)
        elif self._sport == Sport.SOCCER:
            return self._parse_soccer_event(event)
        # TODO: Add parsers for NFL, MLB
        return None
    
    def _parse_nba_event(self, event: dict) -> Optional[NBAGame]:
        """Parse NBA event from ESPN."""
        game = NBAGame()
        
        # Get competition data (first competition in the event)
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        
        # ESPN returns home/away in competitors array
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        
        # Basic info
        game.game_id = str(event.get("id", ""))
        game.home_team = home.get("team", {}).get("displayName", "")
        game.away_team = away.get("team", {}).get("displayName", "")
        game.home_team_id = str(home.get("team", {}).get("id", ""))
        game.away_team_id = str(away.get("team", {}).get("id", ""))
        
        # Scores
        game.home_score = int(home.get("score", 0))
        game.away_score = int(away.get("score", 0))
        
        # Status
        status = competition.get("status", {})
        status_type = status.get("type", {})
        state = status_type.get("state", "pre").lower()
        
        if state == "pre":
            game.status = GameStatus.SCHEDULED
        elif state == "in":
            game.status = GameStatus.LIVE
        elif state == "post":
            game.status = GameStatus.FINAL
        
        # Period/Quarter info
        period = status.get("period", 0)
        game.quarter = period
        
        # Check for overtime
        if period > 4:
            game.is_overtime = True
        
        # Time remaining (only for live games)
        if game.status == GameStatus.LIVE:
            display_clock = status.get("displayClock", "")
            game.time_remaining = display_clock
        
        # Timing
        game.game_date = event.get("date", "")[:10]  # Extract YYYY-MM-DD
        try:
            game.start_time = datetime.fromisoformat(event.get("date", "").replace("Z", "+00:00"))
        except:
            pass
        
        # Venue
        venue = competition.get("venue", {})
        game.venue = venue.get("fullName")
        
        # League info
        game.league = "NBA"
        game.season = event.get("season", {}).get("year")
        
        # Line scores (quarter by quarter)
        home_linescores = home.get("linescores", [])
        away_linescores = away.get("linescores", [])
        
        if home_linescores:
            game.set_quarter_scores(
                [int(ls.get("value", 0)) for ls in home_linescores],
                [int(ls.get("value", 0)) for ls in away_linescores]
            )
        
        # Pregame stats for scrolling text
        home_records = home.get("records", [])
        away_records = away.get("records", [])
        if home_records:
            overall_record = next((r for r in home_records if r.get("type") == "total"), None)
            if overall_record:
                game.home_record = overall_record.get("summary", "")
        if away_records:
            overall_record = next((r for r in away_records if r.get("type") == "total"), None)
            if overall_record:
                game.away_record = overall_record.get("summary", "")
        
        # Average points per game
        home_stats = home.get("statistics", [])
        away_stats = away.get("statistics", [])
        for stat in home_stats:
            if stat.get("name") == "avgPoints":
                try:
                    game.home_avg_points = float(stat.get("displayValue", 0))
                except:
                    pass
            # Top scorer (points per game leader)
            elif stat.get("name") == "pointsPerGame":
                leaders = stat.get("leaders", [])
                if leaders:
                    top_leader = leaders[0]
                    athlete = top_leader.get("athlete", {})
                    game.home_top_scorer = {
                        "name": athlete.get("shortName", ""),
                        "points": top_leader.get("displayValue", "")
                    }
        
        for stat in away_stats:
            if stat.get("name") == "avgPoints":
                try:
                    game.away_avg_points = float(stat.get("displayValue", 0))
                except:
                    pass
            # Top scorer (points per game leader)
            elif stat.get("name") == "pointsPerGame":
                leaders = stat.get("leaders", [])
                if leaders:
                    top_leader = leaders[0]
                    athlete = top_leader.get("athlete", {})
                    game.away_top_scorer = {
                        "name": athlete.get("shortName", ""),
                        "points": top_leader.get("displayValue", "")
                    }
        
        return game
    
    def _parse_ncaab_event(self, event: dict) -> Optional[NCAABGame]:
        """Parse NCAA Men's Basketball event from ESPN (same structure as NBA)."""
        game = NCAABGame()
        
        # Get competition data (first competition in the event)
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        
        # ESPN returns home/away in competitors array
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        
        # Basic info
        game.game_id = str(event.get("id", ""))
        game.home_team = home.get("team", {}).get("displayName", "")
        game.away_team = away.get("team", {}).get("displayName", "")
        game.home_team_id = str(home.get("team", {}).get("id", ""))
        game.away_team_id = str(away.get("team", {}).get("id", ""))
        
        # Scores
        game.home_score = int(home.get("score", 0))
        game.away_score = int(away.get("score", 0))
        
        # Status
        status = competition.get("status", {})
        status_type = status.get("type", {})
        state = status_type.get("state", "pre").lower()
        
        if state == "pre":
            game.status = GameStatus.SCHEDULED
        elif state == "in":
            game.status = GameStatus.LIVE
        elif state == "post":
            game.status = GameStatus.FINAL
        
        # Half info (college uses halves: 1st, 2nd, OT)
        period = status.get("period", 0)
        game.half = period
        
        # Check for overtime (period > 2)
        if period > 2:
            game.is_overtime = True
        
        # Time remaining (only for live games)
        if game.status == GameStatus.LIVE:
            display_clock = status.get("displayClock", "")
            game.time_remaining = display_clock
        
        # Timing
        game.game_date = event.get("date", "")[:10]  # Extract YYYY-MM-DD
        try:
            game.start_time = datetime.fromisoformat(event.get("date", "").replace("Z", "+00:00"))
        except:
            pass
        
        # Venue
        venue = competition.get("venue", {})
        game.venue = venue.get("fullName")
        
        # League info
        game.league = "NCAAB"
        game.season = event.get("season", {}).get("year")
        
        # Line scores (half by half)
        home_linescores = home.get("linescores", [])
        away_linescores = away.get("linescores", [])
        
        if len(home_linescores) >= 2:
            game.home_halves = [
                int(home_linescores[0].get("value", 0)),
                int(home_linescores[1].get("value", 0))
            ]
            game.away_halves = [
                int(away_linescores[0].get("value", 0)),
                int(away_linescores[1].get("value", 0))
            ]
        
        # Pregame stats for scrolling text (same as NBA)
        home_records = home.get("records", [])
        away_records = away.get("records", [])
        if home_records:
            overall_record = next((r for r in home_records if r.get("type") == "total"), None)
            if overall_record:
                game.home_record = overall_record.get("summary", "")
        if away_records:
            overall_record = next((r for r in away_records if r.get("type") == "total"), None)
            if overall_record:
                game.away_record = overall_record.get("summary", "")
        
        # Average points per game
        home_stats = home.get("statistics", [])
        away_stats = away.get("statistics", [])
        for stat in home_stats:
            if stat.get("name") == "avgPoints":
                try:
                    game.home_avg_points = float(stat.get("displayValue", 0))
                except:
                    pass
        for stat in away_stats:
            if stat.get("name") == "avgPoints":
                try:
                    game.away_avg_points = float(stat.get("displayValue", 0))
                except:
                    pass
        
        return game
    
    def _parse_nhl_event(self, event: dict) -> Optional[NHLGame]:
        """Parse ESPN NHL event to NHLGame model."""
        game = NHLGame()
        
        # Get competition data (first competition in the event)
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        
        # Basic game info
        game.game_id = str(event.get("id", ""))
        
        # Find home and away teams
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        
        home_team = home.get("team", {})
        away_team = away.get("team", {})
        
        game.home_team = home_team.get("displayName", "Unknown")
        game.away_team = away_team.get("displayName", "Unknown")
        game.home_team_id = str(home_team.get("id", ""))
        game.away_team_id = str(away_team.get("id", ""))
        
        # Scores
        game.home_score = int(home.get("score", 0))
        game.away_score = int(away.get("score", 0))
        
        # Game status
        status_data = competition.get("status", {})
        status_type = status_data.get("type", {})
        state = status_type.get("state", "pre")
        
        if state == "pre":
            game.status = GameStatus.SCHEDULED
        elif state == "in":
            game.status = GameStatus.LIVE
        else:  # post
            game.status = GameStatus.FINAL
        
        # Period info (for live/final games)
        if game.status == GameStatus.LIVE or game.status == GameStatus.FINAL:
            game.period = int(status_type.get("period", 0))
            
            # Check for OT/SO
            if game.period > 3:
                game.is_overtime = True
                # Check if shootout (ESPN uses "STATUS_SHOOTOUT" or period type)
                detail = status_type.get("detail", "").lower()
                if "shootout" in detail or "so" in detail:
                    game.is_shootout = True
            
            # Time remaining
            display_clock = status_data.get("displayClock", "")
            if display_clock and display_clock != "0:00":
                game.time_remaining = display_clock
        
        # Start time (for scheduled games)
        date_str = competition.get("date")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                game.start_time = dt
            except:
                pass
        
        # Period-by-period scores (linescores)
        home_linescores = home.get("linescores", [])
        away_linescores = away.get("linescores", [])
        
        if home_linescores:
            game.home_periods = [int(ls.get("value", 0)) for ls in home_linescores]
            game.away_periods = [int(ls.get("value", 0)) for ls in away_linescores]
        
        # Additional stats (if available)
        stats = home.get("statistics", [])
        for stat in stats:
            if stat.get("name") == "shots":
                game.home_shots = int(stat.get("displayValue", 0))
            # Top scorer (points leader - goals + assists)
            elif stat.get("name") == "points":
                leaders = stat.get("leaders", [])
                if leaders:
                    top_leader = leaders[0]
                    athlete = top_leader.get("athlete", {})
                    # For NHL, we want to show goals and assists if available
                    game.home_top_scorer = {
                        "name": athlete.get("shortName", ""),
                        "points": top_leader.get("displayValue", "")
                    }
        
        stats = away.get("statistics", [])
        for stat in stats:
            if stat.get("name") == "shots":
                game.away_shots = int(stat.get("displayValue", 0))
            # Top scorer (points leader - goals + assists)
            elif stat.get("name") == "points":
                leaders = stat.get("leaders", [])
                if leaders:
                    top_leader = leaders[0]
                    athlete = top_leader.get("athlete", {})
                    game.away_top_scorer = {
                        "name": athlete.get("shortName", ""),
                        "points": top_leader.get("displayValue", "")
                    }
        
        # Pregame stats for scrolling text
        home_records = home.get("records", [])
        away_records = away.get("records", [])
        if home_records:
            overall_record = next((r for r in home_records if r.get("type") == "total"), None)
            if overall_record:
                game.home_record = overall_record.get("summary", "")  # "32-20-5"
        if away_records:
            overall_record = next((r for r in away_records if r.get("type") == "total"), None)
            if overall_record:
                game.away_record = overall_record.get("summary", "")  # "29-20-7"
        
        return game
    
    def _parse_soccer_event(self, event: dict) -> Optional[SoccerGame]:
        """Parse ESPN soccer event to SoccerGame model."""
        game = SoccerGame()
        
        # Get competition data
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        
        # Basic game info
        game.game_id = str(event.get("id", ""))
        
        # Find home and away teams
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        
        home_team = home.get("team", {})
        away_team = away.get("team", {})
        
        game.home_team = home_team.get("displayName", "Unknown")
        game.away_team = away_team.get("displayName", "Unknown")
        game.home_team_id = str(home_team.get("id", ""))
        game.away_team_id = str(away_team.get("id", ""))
        
        # Scores
        game.home_score = int(home.get("score", 0))
        game.away_score = int(away.get("score", 0))
        
        # Game status
        status_data = competition.get("status", {})
        status_type = status_data.get("type", {})
        state = status_type.get("state", "pre")
        
        if state == "pre":
            game.status = GameStatus.SCHEDULED
        elif state == "in":
            game.status = GameStatus.LIVE
        else:  # post
            game.status = GameStatus.FINAL
        
        # Match time (for live/final games)
        if game.status == GameStatus.LIVE or game.status == GameStatus.FINAL:
            # Period (half)
            period = int(status_type.get("period", 0))
            game.half = period
            
            # Match minute
            display_clock = status_data.get("displayClock", "")
            if display_clock:
                game.minute = display_clock
                
                # If period is 0 but we have a minute, infer the half
                if game.half == 0 and display_clock:
                    try:
                        # Parse minute (e.g., "20'" or "45'+2")
                        minute_str = display_clock.replace("'", "").split("+")[0]
                        minute_num = int(minute_str)
                        if minute_num <= 45:
                            game.half = 1
                        else:
                            game.half = 2
                    except:
                        game.half = 1  # Default to first half
            
            # Check for halftime, extra time or penalties
            detail = status_type.get("detail", "").lower()
            
            # Debug: log detail to see what ESPN sends
            if "half" in detail or "time" in detail or detail == "ht":
                print(f"[DEBUG SOCCER] status detail: {detail}, period: {period}, clock: {display_clock}")
            
            if "ht" in detail or "halftime" in detail:
                game.minute = "HT"  # Show "HT" for halftime
            elif "extra time" in detail or "et" in detail:
                game.is_extra_time = True
            if "penalties" in detail or "penalty shootout" in detail:
                game.is_penalty_shootout = True
        
        # Start time (for scheduled games)
        date_str = competition.get("date")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                game.start_time = dt
            except:
                pass
        
        # League info
        league_data = event.get("league", {})
        game.league = league_data.get("name", "Soccer")
        
        # Half-by-half scores (linescores)
        home_linescores = home.get("linescores", [])
        away_linescores = away.get("linescores", [])
        
        if home_linescores:
            game.home_halves = [int(ls.get("value", 0)) for ls in home_linescores]
            game.away_halves = [int(ls.get("value", 0)) for ls in away_linescores]
        
        # Additional stats
        stats = home.get("statistics", [])
        for stat in stats:
            name = stat.get("name", "")
            if name == "shots":
                game.home_shots = int(stat.get("displayValue", 0))
            elif name == "corners":
                game.home_corners = int(stat.get("displayValue", 0))
            elif name == "redCards":
                game.home_red_cards = int(stat.get("displayValue", 0))
        
        stats = away.get("statistics", [])
        for stat in stats:
            name = stat.get("name", "")
            if name == "shots":
                game.away_shots = int(stat.get("displayValue", 0))
            elif name == "corners":
                game.away_corners = int(stat.get("displayValue", 0))
            elif name == "redCards":
                game.away_red_cards = int(stat.get("displayValue", 0))
        
        return game
