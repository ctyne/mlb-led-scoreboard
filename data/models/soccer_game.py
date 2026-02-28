"""Soccer/Football game model with match-specific properties."""

from datetime import datetime
from typing import Optional
from data.models.base_game import BaseGame, GameStatus, Sport


class SoccerGame(BaseGame):
    """Soccer/Football game model with match-specific properties."""
    
    def __init__(self):
        super().__init__()
        self.sport = Sport.SOCCER
        
        # Soccer-specific fields
        self.half: int = 0  # 1 or 2 for halves, 3+ for extra time
        self.minute: str = ""  # "45'+2" or "67" format
        self.is_extra_time: bool = False
        self.is_penalty_shootout: bool = False
        
        # Half-by-half scores
        self.home_halves: list[int] = []
        self.away_halves: list[int] = []
        
        # Additional stats (optional)
        self.home_shots: int = 0
        self.away_shots: int = 0
        self.home_corners: int = 0
        self.away_corners: int = 0
        self.home_red_cards: int = 0
        self.away_red_cards: int = 0
        
        # League info
        self.league: str = ""  # "Premier League", "MLS", etc.
    
    def get_period_label(self) -> str:
        """Get user-friendly period label (1st Half, 2nd Half, ET, PK)."""
        if self.is_penalty_shootout:
            return "PK"
        elif self.is_extra_time:
            return "ET"
        elif self.half == 1:
            return "1st Half"
        elif self.half == 2:
            return "2nd Half"
        else:
            return f"H{self.half}"
    
    def get_time_remaining(self) -> Optional[str]:
        """Get match time (soccer doesn't have 'time remaining', returns current minute)."""
        if self.is_live() and self.minute:
            return self.minute
        return None
    
    def get_sport_specific_data(self) -> dict:
        """Return soccer-specific data."""
        return {
            'half': self.half,
            'minute': self.minute,
            'is_extra_time': self.is_extra_time,
            'is_penalty_shootout': self.is_penalty_shootout,
            'home_halves': self.home_halves,
            'away_halves': self.away_halves,
            'home_shots': self.home_shots,
            'away_shots': self.away_shots,
            'home_corners': self.home_corners,
            'away_corners': self.away_corners,
            'home_red_cards': self.home_red_cards,
            'away_red_cards': self.away_red_cards,
            'league': self.league
        }
    
    def get_match_time(self) -> str:
        """Get formatted match time."""
        if self.minute:
            return self.minute
        return ""
    
    def is_live(self) -> bool:
        """Check if match is currently live."""
        return self.status == GameStatus.LIVE
    
    def is_final(self) -> bool:
        """Check if match is final."""
        return self.status == GameStatus.FINAL
    
    def is_scheduled(self) -> bool:
        """Check if match is scheduled but not started."""
        return self.status == GameStatus.SCHEDULED
    
    def get_half_scores(self, team: str = 'home') -> list[int]:
        """Get half-by-half scores for a team."""
        if team.lower() == 'home':
            return self.home_halves
        else:
            return self.away_halves
    
    def __repr__(self) -> str:
        return (
            f"SoccerGame(id={self.game_id}, {self.away_team}@{self.home_team}, "
            f"status={self.status.value}, {self.away_score}-{self.home_score}, "
            f"time={self.get_match_time()})"
        )
