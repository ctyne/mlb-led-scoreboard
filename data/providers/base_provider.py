"""
Base provider interface for fetching game data from various APIs.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import date
from data.models.base_game import BaseGame, Sport


class BaseProvider(ABC):
    """
    Abstract base class for all sport data providers.
    Each API (TheSportsDB, statsapi, ESPN, etc.) implements this interface.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize provider with optional API key.
        
        Args:
            api_key: API key for services that require authentication
        """
        self.api_key = api_key
        self._cache = {}  # Simple in-memory cache
    
    @abstractmethod
    def get_sport(self) -> Sport:
        """Return the sport this provider handles."""
        pass
    
    @abstractmethod
    def get_games_for_date(self, game_date: date, team_ids: Optional[List[str]] = None) -> List[BaseGame]:
        """
        Fetch all games for a specific date, optionally filtered by team IDs.
        
        Args:
            game_date: The date to fetch games for
            team_ids: Optional list of team IDs to filter by
            
        Returns:
            List of BaseGame objects for the given date
        """
        pass
    
    @abstractmethod
    def get_game_details(self, game_id: str) -> Optional[BaseGame]:
        """
        Fetch detailed information for a specific game.
        
        Args:
            game_id: The unique identifier for the game
            
        Returns:
            BaseGame object with full details, or None if not found
        """
        pass
    
    @abstractmethod
    def search_teams(self, query: str) -> List[Dict[str, str]]:
        """
        Search for teams by name.
        
        Args:
            query: Team name search query
            
        Returns:
            List of team dictionaries with 'id', 'name', 'abbreviation'
        """
        pass
    
    def get_live_games(self, team_ids: Optional[List[str]] = None) -> List[BaseGame]:
        """
        Get all currently live games, optionally filtered by team IDs.
        
        Args:
            team_ids: Optional list of team IDs to filter by
            
        Returns:
            List of live BaseGame objects
        """
        from datetime import date
        today = date.today()
        all_games = self.get_games_for_date(today, team_ids)
        return [game for game in all_games if game.is_live()]
    
    def clear_cache(self):
        """Clear the provider's cache."""
        self._cache = {}
