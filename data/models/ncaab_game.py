"""
NCAA Men's Basketball game model.
Nearly identical to NBA but for college basketball.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from data.models.base_game import BaseGame, GameStatus, Sport


class NCAABGame(BaseGame):
    """NCAA Men's Basketball game model."""
    
    def __init__(self):
        super().__init__()
        self.sport = Sport.NCAAB
        
        # Basketball-specific properties (same as NBA)
        self.half: int = 0  # 1 or 2, or 3+ for overtime
        self.time_remaining: Optional[str] = None  # Format: "5:23"
        self.is_overtime: bool = False
        
        # Half scores
        self.home_halves: list = [0, 0]  # 1st half, 2nd half
        self.away_halves: list = [0, 0]
        
        # Additional stats
        self.home_fouls: int = 0
        self.away_fouls: int = 0
        
        # Pregame stats for scrolling text
        self.away_record: Optional[str] = None  # "22-5"
        self.home_record: Optional[str] = None  # "18-9"
        self.away_avg_points: Optional[float] = None
        self.home_avg_points: Optional[float] = None
        
    def get_period_label(self) -> str:
        """Get current half/period label."""
        if self.status == GameStatus.SCHEDULED:
            return "Scheduled"
        elif self.status == GameStatus.FINAL:
            return "Final"
        elif self.is_overtime:
            ot_number = self.half - 2
            return f"OT{ot_number}" if ot_number > 1 else "OT"
        elif self.half == 1:
            return "1H"
        elif self.half == 2:
            return "2H"
        else:
            return "Unknown"
    
    def get_time_remaining(self) -> Optional[str]:
        """Get time remaining in current half."""
        if self.is_live() and self.time_remaining:
            return self.time_remaining
        return None
    
    def get_sport_specific_data(self) -> Dict[str, Any]:
        """Return college basketball-specific data."""
        return {
            'half': self.half,
            'time_remaining': self.time_remaining,
            'is_overtime': self.is_overtime,
            'home_halves': self.home_halves,
            'away_halves': self.away_halves,
            'home_fouls': self.home_fouls,
            'away_fouls': self.away_fouls
        }
    
    def is_live(self) -> bool:
        """Check if game is currently in progress."""
        return self.status == GameStatus.LIVE
    
    def is_final(self) -> bool:
        """Check if game is finished."""
        return self.status == GameStatus.FINAL
    
    def __str__(self):
        return f"NCAAB: {self.away_team} ({self.away_score}) @ {self.home_team} ({self.home_score}) - {self.status.value}"
