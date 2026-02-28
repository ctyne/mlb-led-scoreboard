"""
Multi-sport data wrapper that combines MLB and other sports.
Integrates with the existing Data class structure.
"""

from typing import List, Optional
from datetime import date

from data.models.base_game import Sport
from data.providers.espn_provider import ESPNProvider
from data.scheduler import GameScheduler


class MultiSportData:
    """
    Wrapper that adds multi-sport support to the scoreboard.
    Combines MLB (existing) with NBA, NHL, NFL via ESPN API.
    """
    
    def __init__(self, config):
        """
        Initialize multi-sport data handler.
        
        Args:
            config: The existing Config object
        """
        self.config = config
        self.enabled = getattr(config, 'multi_sport_enabled', False)
        
        if not self.enabled:
            # Multi-sport disabled, return early
            self.scheduler = None
            return
        
        # Get configuration
        self.sports = getattr(config, 'multi_sport_sports', ['MLB', 'NBA'])
        self.favorite_teams = getattr(config, 'multi_sport_favorite_teams', {})
        
        # Initialize providers for each enabled sport (except MLB which uses statsapi)
        self.providers = []
        
        if 'NBA' in self.sports:
            nba_provider = ESPNProvider(Sport.NBA)
            self.providers.append(nba_provider)
        
        if 'NHL' in self.sports:
            nhl_provider = ESPNProvider(Sport.NHL)
            self.providers.append(nhl_provider)
        
        if 'NFL' in self.sports:
            nfl_provider = ESPNProvider(Sport.NFL)
            self.providers.append(nfl_provider)
        
        if 'SOCCER' in self.sports:
            soccer_provider = ESPNProvider(Sport.SOCCER)
            self.providers.append(soccer_provider)
        
        # Create team ID mappings for filtering
        favorite_team_ids = {}
        for sport_str, teams in self.favorite_teams.items():
            sport = self._str_to_sport(sport_str)
            if sport:
                favorite_team_ids[sport] = [str(team.get('id', '')) for team in teams]
        
        # Initialize scheduler
        self.scheduler = GameScheduler(self.providers, favorite_team_ids)
    
    def get_todays_games(self, refresh: bool = False):
        """
        Get all games for today across enabled sports.
        
        Args:
            refresh: Force refresh from APIs
            
        Returns:
            List of games (MLB excluded - handled separately)
        """
        if not self.enabled or not self.scheduler:
            return []
        
        return self.scheduler.get_todays_games(refresh=refresh)
    
    def get_live_games(self):
        """Get all currently live games (non-MLB)."""
        if not self.enabled or not self.scheduler:
            return []
        
        return self.scheduler.get_live_games()
    
    def has_live_games(self):
        """Check if there are any live non-MLB games."""
        return len(self.get_live_games()) > 0
    
    def _str_to_sport(self, sport_str: str) -> Optional[Sport]:
        """Convert string to Sport enum."""
        mapping = {
            'NBA': Sport.NBA,
            'NHL': Sport.NHL,
            'NFL': Sport.NFL,
            'MLB': Sport.MLB,
            'SOCCER': Sport.SOCCER
        }
        return mapping.get(sport_str.upper())
