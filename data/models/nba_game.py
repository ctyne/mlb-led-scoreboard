"""
NBA-specific game model.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from data.models.base_game import BaseGame, GameStatus, Sport


class NBAGame(BaseGame):
    """NBA game model with basketball-specific properties."""
    
    def __init__(self):
        super().__init__()
        self.sport = Sport.NBA
        
        # NBA-specific properties
        self.quarter: int = 0  # 1-4, or 5+ for overtime
        self.time_remaining: Optional[str] = None  # Format: "5:23"
        self.is_overtime: bool = False
        
        # Quarter scores (for detailed display)
        self.home_quarters: list = [0, 0, 0, 0]  # Q1, Q2, Q3, Q4
        self.away_quarters: list = [0, 0, 0, 0]
        
        # Additional stats
        self.home_fouls: int = 0
        self.away_fouls: int = 0
        
        # Pregame stats for scrolling text
        self.away_record: Optional[str] = None  # "28-31"
        self.home_record: Optional[str] = None  # "15-44"
        self.away_avg_points: Optional[float] = None  # 115.9
        self.home_avg_points: Optional[float] = None  # 111.5
        
    def get_period_label(self) -> str:
        """Get current quarter label."""
        if self.status == GameStatus.SCHEDULED:
            return "Scheduled"
        elif self.status == GameStatus.FINAL:
            return "Final"
        elif self.is_overtime:
            ot_number = self.quarter - 4
            return f"OT{ot_number}" if ot_number > 1 else "OT"
        elif self.quarter > 0:
            return f"Q{self.quarter}"
        else:
            return "Unknown"
    
    def get_time_remaining(self) -> Optional[str]:
        """Get time remaining in current quarter."""
        if self.is_live() and self.time_remaining:
            return self.time_remaining
        return None
    
    def get_sport_specific_data(self) -> Dict[str, Any]:
        """Get NBA-specific data."""
        return {
            "quarter": self.quarter,
            "time_remaining": self.time_remaining,
            "is_overtime": self.is_overtime,
            "home_quarters": self.home_quarters,
            "away_quarters": self.away_quarters,
            "fouls": {
                "home": self.home_fouls,
                "away": self.away_fouls
            }
        }
    
    def set_quarter_scores(self, home_scores: list, away_scores: list):
        """
        Set quarter-by-quarter scores.
        
        Args:
            home_scores: List of scores for each quarter [Q1, Q2, Q3, Q4, OT1, ...]
            away_scores: List of scores for each quarter
        """
        # Ensure we have at least 4 quarters
        while len(home_scores) < 4:
            home_scores.append(0)
        while len(away_scores) < 4:
            away_scores.append(0)
            
        self.home_quarters = home_scores[:4]
        self.away_quarters = away_scores[:4]
        
        # Check if there are overtime periods
        if len(home_scores) > 4 or len(away_scores) > 4:
            self.is_overtime = True
