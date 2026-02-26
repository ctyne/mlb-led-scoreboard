"""
Base game model that all sport-specific games extend.
Provides common interface for displaying any sport on the scoreboard.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class GameStatus(Enum):
    """Game status across all sports."""
    SCHEDULED = "scheduled"  # Game hasn't started yet
    LIVE = "live"           # Game in progress
    FINAL = "final"         # Game finished
    POSTPONED = "postponed" # Game delayed
    CANCELLED = "cancelled" # Game cancelled


class Sport(Enum):
    """Supported sports."""
    MLB = "mlb"
    NBA = "nba"
    NCAAB = "ncaab"  # NCAA Men's Basketball
    NHL = "nhl"
    NFL = "nfl"
    SOCCER = "soccer"  # EFL and other soccer leagues


class BaseGame(ABC):
    """
    Abstract base class for all sport games.
    Each sport implements this interface with sport-specific details.
    """
    
    def __init__(self):
        # Common properties across all sports
        self.sport: Sport = None
        self.game_id: str = None
        self.status: GameStatus = GameStatus.SCHEDULED
        
        # Teams
        self.home_team: str = None
        self.away_team: str = None
        self.home_team_id: str = None
        self.away_team_id: str = None
        
        # Scores
        self.home_score: int = 0
        self.away_score: int = 0
        
        # Timing
        self.start_time: Optional[datetime] = None
        self.game_date: Optional[str] = None  # YYYY-MM-DD format
        
        # Venue
        self.venue: Optional[str] = None
        self.city: Optional[str] = None
        
        # Additional metadata
        self.league: Optional[str] = None
        self.season: Optional[str] = None
        
    @abstractmethod
    def get_period_label(self) -> str:
        """
        Get the current period label for this sport.
        Examples: "Top 3rd" (MLB), "Q2" (NBA/NFL), "2nd Period" (NHL), "1st Half" (Soccer)
        """
        pass
    
    @abstractmethod
    def get_time_remaining(self) -> Optional[str]:
        """
        Get formatted time remaining in current period.
        Returns None if not applicable (e.g., baseball has no clock).
        Examples: "5:23" (NBA/NHL/NFL), "45:00" (Soccer), None (MLB)
        """
        pass
    
    @abstractmethod
    def get_sport_specific_data(self) -> Dict[str, Any]:
        """
        Get sport-specific data that doesn't fit the common model.
        Examples: 
        - MLB: {"inning": 3, "outs": 2, "on_base": [1,3]}
        - NBA: {"quarter": 2, "fouls": {"home": 3, "away": 4}}
        - NHL: {"period": 2, "power_play": True}
        - NFL: {"quarter": 3, "down": 2, "yards_to_go": 7}
        - Soccer: {"half": 1, "extra_time": False}
        """
        pass
    
    def is_live(self) -> bool:
        """Check if game is currently in progress."""
        return self.status == GameStatus.LIVE
    
    def is_final(self) -> bool:
        """Check if game is finished."""
        return self.status == GameStatus.FINAL
    
    def is_scheduled(self) -> bool:
        """Check if game hasn't started yet."""
        return self.status == GameStatus.SCHEDULED
    
    def get_display_name(self) -> str:
        """Get formatted game name for display."""
        return f"{self.away_team} @ {self.home_team}"
    
    def get_score_summary(self) -> str:
        """Get formatted score summary."""
        return f"{self.away_team} {self.away_score} - {self.home_score} {self.home_team}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.get_display_name()} ({self.status.value})>"
