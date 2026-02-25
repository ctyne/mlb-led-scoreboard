"""
Game scheduler that combines games from multiple sports.
Fetches and prioritizes games based on favorite teams and live status.
"""

from typing import List, Optional
from datetime import date, datetime
from data.models.base_game import BaseGame, GameStatus, Sport
from data.providers.base_provider import BaseProvider


class GameScheduler:
    """
    Centralized scheduler for multi-sport games.
    Combines games from multiple providers and prioritizes them.
    """
    
    def __init__(self, providers: List[BaseProvider], favorite_team_ids: Optional[dict] = None):
        """
        Initialize the game scheduler.
        
        Args:
            providers: List of sport providers (MLB, NBA, NHL, etc.)
            favorite_team_ids: Dict mapping Sport -> List of team IDs
                Example: {Sport.NBA: ["134871"], Sport.MLB: ["147"]}
        """
        self.providers = providers
        self.favorite_team_ids = favorite_team_ids or {}
        self._cache = {}
        self._cache_time = None
    
    def get_todays_games(self, refresh: bool = False) -> List[BaseGame]:
        """
        Get all games for today across all sports.
        
        Args:
            refresh: Force refresh from APIs (ignore cache)
            
        Returns:
            List of BaseGame objects sorted by priority
        """
        today = date.today()
        cache_key = f"games_{today}"
        
        # Check cache (5 minute cache for live games)
        if not refresh and cache_key in self._cache:
            if self._cache_time:
                age = (datetime.now() - self._cache_time).total_seconds()
                if age < 300:  # 5 minutes
                    return self._cache[cache_key]
        
        # Fetch games from all providers
        all_games = []
        for provider in self.providers:
            sport = provider.get_sport()
            team_ids = self.favorite_team_ids.get(sport)
            
            try:
                games = provider.get_games_for_date(today, team_ids)
                all_games.extend(games)
            except Exception as e:
                print(f"Error fetching {sport.value} games: {e}")
        
        # Sort by priority
        sorted_games = self._prioritize_games(all_games)
        
        # Update cache
        self._cache[cache_key] = sorted_games
        self._cache_time = datetime.now()
        
        return sorted_games
    
    def get_live_games(self) -> List[BaseGame]:
        """Get all currently live games across all sports."""
        all_games = self.get_todays_games()
        return [game for game in all_games if game.is_live()]
    
    def _prioritize_games(self, games: List[BaseGame]) -> List[BaseGame]:
        """
        Sort games by priority.
        Priority order: Live > Scheduled (by start time) > Final
        """
        def priority_key(game: BaseGame):
            # Live games first (lowest number = highest priority)
            if game.status == GameStatus.LIVE:
                return (0, game.start_time or datetime.min)
            # Scheduled games next, sorted by start time
            elif game.status == GameStatus.SCHEDULED:
                return (1, game.start_time or datetime.max)
            # Final games last
            else:
                return (2, game.start_time or datetime.max)
        
        return sorted(games, key=priority_key)
    
    def clear_cache(self):
        """Clear the game cache."""
        self._cache = {}
        self._cache_time = None
