"""NHL game model with hockey-specific properties."""

from datetime import datetime
from typing import Optional
from data.models.base_game import BaseGame, GameStatus, Sport


class NHLGame(BaseGame):
    """NHL game model with hockey-specific properties."""
    
    def __init__(self):
        super().__init__()
        self.sport = Sport.NHL
        
        # NHL-specific fields
        self.period: int = 0  # 1-3 for regulation, 4+ for OT
        self.time_remaining: str = ""  # "12:34" format
        self.is_overtime: bool = False
        self.is_shootout: bool = False
        
        # Period-by-period scores
        self.home_periods: list[int] = []
        self.away_periods: list[int] = []
        
        # Additional stats (optional)
        self.home_shots: int = 0
        self.away_shots: int = 0
        self.home_powerplay: bool = False
        self.away_powerplay: bool = False
        
        # Pregame stats for scrolling text
        self.away_record: Optional[str] = None  # "29-20-7"
        self.home_record: Optional[str] = None  # "32-20-5"
    
    def get_period_label(self) -> str:
        """Get user-friendly period label (P1, P2, P3, OT, SO)."""
        if self.is_shootout:
            return "SO"
        elif self.is_overtime:
            if self.period == 4:
                return "OT"
            else:
                # Multiple OTs (rare in regular season, common in playoffs)
                return f"{self.period - 3}OT"
        elif self.period <= 3:
            return f"P{self.period}"
        else:
            return f"P{self.period}"
    
    def get_time_remaining(self) -> Optional[str]:
        """Get time remaining in current period."""
        if self.is_live() and self.time_remaining:
            return self.time_remaining
        return None
    
    def get_sport_specific_data(self) -> dict:
        """Return NHL-specific data."""
        return {
            'period': self.period,
            'time_remaining': self.time_remaining,
            'is_overtime': self.is_overtime,
            'is_shootout': self.is_shootout,
            'home_periods': self.home_periods,
            'away_periods': self.away_periods,
            'home_shots': self.home_shots,
            'away_shots': self.away_shots,
            'home_powerplay': self.home_powerplay,
            'away_powerplay': self.away_powerplay
        }
    
    def is_live(self) -> bool:
        """Check if game is currently live."""
        return self.status == GameStatus.LIVE
    
    def is_final(self) -> bool:
        """Check if game is final."""
        return self.status == GameStatus.FINAL
    
    def is_scheduled(self) -> bool:
        """Check if game is scheduled but not started."""
        return self.status == GameStatus.SCHEDULED
    
    def get_period_scores(self, team: str = 'home') -> list[int]:
        """Get period-by-period scores for a team."""
        if team.lower() == 'home':
            return self.home_periods
        else:
            return self.away_periods
    
    def __repr__(self) -> str:
        return (
            f"NHLGame(id={self.game_id}, {self.away_team}@{self.home_team}, "
            f"status={self.status.value}, {self.away_score}-{self.home_score}, "
            f"period={self.get_period_label()})"
        )
