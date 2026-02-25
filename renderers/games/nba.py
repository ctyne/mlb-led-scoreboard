"""
Simple NBA game renderer.
Displays NBA games on the LED matrix using text.
"""

from renderers.game import GameRenderer
from data.models.nba_game import NBAGame


class NBAGameRenderer(GameRenderer):
    """Renderer for NBA games on LED display."""
    
    def __init__(self, matrix, data):
        super().__init__(matrix, data)
    
    def render(self):
        """Render NBA game on the LED matrix."""
        game = self.data.current_other_sport_game
        
        if not isinstance(game, NBAGame):
            return
        
        # Clear the display
        self.canvas.Clear()
        
        # Use the graphics library from the driver
        from driver import graphics
        
        # Load a small font
        font = graphics.Font()
        font.LoadFont(self.layout.font("pregame.scrolling_text.font")["font"])
        
        # Colors
        white = graphics.Color(255, 255, 255)
        red = graphics.Color(255, 0, 0)
        green = graphics.Color(0, 255, 0)
        
        # Display game info
        y_pos = 8
        
        # Sport indicator
        graphics.DrawText(self.canvas, font, 1, y_pos, green, "NBA")
        y_pos += 7
        
        # Team names (abbreviated if needed)
        away_abbrev = self._abbreviate_team(game.away_team)
        home_abbrev = self._abbreviate_team(game.home_team)
        
        game_text = f"{away_abbrev} @ {home_abbrev}"
        graphics.DrawText(self.canvas, font, 1, y_pos, white, game_text)
        y_pos += 7
        
        # Score
        if game.is_live():
            score_text = f"{game.away_score}-{game.home_score} {game.get_period_label()}"
            graphics.DrawText(self.canvas, font, 1, y_pos, red, score_text)
            y_pos += 7
            
            # Time remaining if available
            if game.time_remaining:
                graphics.DrawText(self.canvas, font, 1, y_pos, white, game.time_remaining)
        elif game.is_final():
            score_text = f"FINAL {game.away_score}-{game.home_score}"
            graphics.DrawText(self.canvas, font, 1, y_pos, white, score_text)
        else:
            # Scheduled
            graphics.DrawText(self.canvas, font, 1, y_pos, white, game.get_period_label())
        
        # Swap canvas
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def _abbreviate_team(self, team_name):
        """Abbreviate team name to fit on display."""
        # Common abbreviations
        abbrevs = {
            "Atlanta Hawks": "ATL",
            "Boston Celtics": "BOS",
            "Brooklyn Nets": "BKN",
            "Charlotte Hornets": "CHA",
            "Chicago Bulls": "CHI",
            "Cleveland Cavaliers": "CLE",
            "Dallas Mavericks": "DAL",
            "Denver Nuggets": "DEN",
            "Detroit Pistons": "DET",
            "Golden State Warriors": "GSW",
            "Houston Rockets": "HOU",
            "Indiana Pacers": "IND",
            "LA Clippers": "LAC",
            "Los Angeles Lakers": "LAL",
            "Memphis Grizzlies": "MEM",
            "Miami Heat": "MIA",
            "Milwaukee Bucks": "MIL",
            "Minnesota Timberwolves": "MIN",
            "New Orleans Pelicans": "NOP",
            "New York Knicks": "NYK",
            "Oklahoma City Thunder": "OKC",
            "Orlando Magic": "ORL",
            "Philadelphia 76ers": "PHI",
            "Phoenix Suns": "PHX",
            "Portland Trail Blazers": "POR",
            "Sacramento Kings": "SAC",
            "San Antonio Spurs": "SAS",
            "Toronto Raptors": "TOR",
            "Utah Jazz": "UTA",
            "Washington Wizards": "WAS"
        }
        
        return abbrevs.get(team_name, team_name[:3].upper())
