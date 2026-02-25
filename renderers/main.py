import time
from typing import Callable, NoReturn
from data.screens import ScreenType

import debug
from data import Data, status
from data.scoreboard import Scoreboard
from data.scoreboard.postgame import Postgame
from data.scoreboard.pregame import Pregame
from renderers import network, offday, standings
from renderers.games import game as gamerender
from renderers.games import irregular
from renderers.games import postgame as postgamerender
from renderers.games import pregame as pregamerender
from renderers.games import teams

# TODO(BMW) make configurable time?
STANDINGS_NEWS_SWITCH_TIME = 120


class MainRenderer:
    def __init__(self, matrix, data):
        self.matrix = matrix
        self.data: Data = data
        self.is_playoffs = self.data.schedule.date > self.data.headlines.important_dates.playoffs_start_date.date()
        self.canvas = matrix.CreateFrameCanvas()
        self.scrolling_text_pos = self.canvas.width
        self.game_changed_time = time.time()
        self.animation_time = 0
        self.standings_stat = "w"
        self.standings_league = "NL"

    def render(self):
        screen = self.data.get_screen_type()
        # display the news ticker
        if screen == ScreenType.ALWAYS_NEWS:
            self.__draw_news(permanent_cond)
        # display the standings
        elif screen == ScreenType.ALWAYS_STANDINGS:
            self.__render_standings()
        elif screen == ScreenType.LEAGUE_OFFDAY:
            self.__render_offday(team_offday=False)
        elif screen == ScreenType.PREFERRED_TEAM_OFFDAY:
            self.__render_offday(team_offday=True)
        # Playball!
        else:
            self.__render_gameday()

    def __render_offday(self, team_offday=True) -> NoReturn:
        if team_offday:
            news = self.data.config.news_ticker_team_offday
            standings = self.data.config.standings_team_offday
        else:
            news = True
            standings = self.data.config.standings_mlb_offday

        if news and standings:
            while True:
                self.__draw_news(timer_cond(STANDINGS_NEWS_SWITCH_TIME))
                self.__draw_standings(timer_cond(STANDINGS_NEWS_SWITCH_TIME))
        elif news:
            self.__draw_news(permanent_cond)
        else:
            self.__render_standings()

    def __render_standings(self) -> NoReturn:
        self.__draw_standings(permanent_cond)

        # Out of season off days don't always return standings so fall back on the news renderer
        debug.error("No standings data.  Falling back to news.")
        self.__draw_news(permanent_cond)

    # Renders a game screen based on it's status
    # May also call draw_offday or draw_standings if there are no games
    def __render_gameday(self) -> NoReturn:
        refresh_rate = self.data.config.scrolling_speed
        while True:
            if not self.data.schedule.games_live():
                if self.data.config.news_no_games and self.data.config.standings_no_games:
                    self.__draw_news(all_of(timer_cond(STANDINGS_NEWS_SWITCH_TIME), self.no_games_cond))
                    self.__draw_standings(all_of(timer_cond(STANDINGS_NEWS_SWITCH_TIME), self.no_games_cond))
                    continue
                elif self.data.config.news_no_games:
                    self.__draw_news(self.no_games_cond)
                elif self.data.config.standings_no_games:
                    self.__draw_standings(self.no_games_cond)

            if self.game_changed_time < self.data.game_changed_time:
                self.scrolling_text_pos = self.canvas.width
                self.data.scrolling_finished = not self.data.config.rotation_scroll_until_finished
                self.game_changed_time = time.time()

            # Draw the current game
            self.__draw_game()

            time.sleep(refresh_rate)

    # Draws the provided game on the canvas
    def __draw_game(self):
        # Check if we're showing a non-MLB game
        if self.data.current_game_is_other_sport and self.data.current_other_sport_game:
            self.__draw_other_sport_game()
            return
        
        game = self.data.current_game
        if game is None:
            # This can happen briefly during transitions between MLB and other sports
            return
        bgcolor = self.data.config.scoreboard_colors.color("default.background")
        self.canvas.Fill(bgcolor["r"], bgcolor["g"], bgcolor["b"])
        scoreboard = Scoreboard(game)
        layout = self.data.config.layout
        colors = self.data.config.scoreboard_colors

        if status.is_pregame(game.status()):  # Draw the pregame information
            self.__max_scroll_x(layout.coords("pregame.scrolling_text"))
            pregame = Pregame(game, self.data.config.time_format)
            pos = pregamerender.render_pregame(
                self.canvas,
                layout,
                colors,
                pregame,
                self.scrolling_text_pos,
                self.data.config.pregame_weather,
                self.is_playoffs,
            )
            self.__update_scrolling_text_pos(pos, self.canvas.width)

        elif status.is_complete(game.status()):  # Draw the game summary
            self.__max_scroll_x(layout.coords("final.scrolling_text"))
            final = Postgame(game)
            pos = postgamerender.render_postgame(
                self.canvas, layout, colors, final, scoreboard, self.scrolling_text_pos, self.is_playoffs
            )
            self.__update_scrolling_text_pos(pos, self.canvas.width)

        elif status.is_irregular(game.status()):  # Draw game status
            short_text = self.data.config.layout.coords("status.text")["short_text"]
            if scoreboard.get_text_for_reason():
                self.__max_scroll_x(layout.coords("status.scrolling_text"))
                pos = irregular.render_irregular_status(
                    self.canvas, layout, colors, scoreboard, short_text, self.scrolling_text_pos
                )
                self.__update_scrolling_text_pos(pos, self.canvas.width)
            else:
                irregular.render_irregular_status(self.canvas, layout, colors, scoreboard, short_text)
                self.data.scrolling_finished = True

        else:  # draw a live game
            if scoreboard.homerun() or scoreboard.strikeout() or scoreboard.hit() or scoreboard.walk():
                self.animation_time += 1
            else:
                self.animation_time = 0

            if status.is_inning_break(scoreboard.inning.state):
                loop_point = self.data.config.layout.coords("inning.break.due_up")["loop"]
            else:
                loop_point = self.data.config.layout.coords("atbat")["loop"]

            self.scrolling_text_pos = min(self.scrolling_text_pos, loop_point)
            pos = gamerender.render_live_game(
                self.canvas, layout, colors, scoreboard, self.scrolling_text_pos, self.animation_time
            )
            self.__update_scrolling_text_pos(pos, loop_point)

        # draw last so it is always on top
        teams.render_team_banner(
            self.canvas,
            layout,
            self.data.config.team_colors,
            scoreboard.home_team,
            scoreboard.away_team,
            self.data.config.full_team_names,
            self.data.config.short_team_names_for_runs_hits,
            show_score=not status.is_pregame(game.status()),
        )

        # Show network issues
        if self.data.network_issues:
            network.render_network_error(self.canvas, layout, colors)

        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def __draw_news(self, cond: Callable[[], bool]):
        """
        Draw the news screen for as long as cond returns True
        """
        color = self.data.config.scoreboard_colors.color("default.background")
        while cond():
            self.canvas.Fill(color["r"], color["g"], color["b"])

            self.__max_scroll_x(self.data.config.layout.coords("offday.scrolling_text"))
            pos = offday.render_offday_screen(
                self.canvas,
                self.data.config.layout,
                self.data.config.scoreboard_colors,
                self.data.weather,
                self.data.headlines,
                self.data.config.time_format,
                self.scrolling_text_pos,
            )
            # todo make scrolling_text_pos something persistent/news-specific
            # if we want to show news as part of rotation?
            # not strictly necessary but would be nice, avoids only seeing first headline over and over
            self.__update_scrolling_text_pos(pos, self.canvas.width)
            # Show network issues
            if self.data.network_issues:
                network.render_network_error(self.canvas, self.data.config.layout, self.data.config.scoreboard_colors)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            time.sleep(self.data.config.scrolling_speed)

    def __draw_standings(self, cond: Callable[[], bool]):
        """
        Draw the standings screen for as long as cond returns True
        """
        if not self.data.standings.populated():
            return

        if self.data.standings.is_postseason() and self.canvas.width <= 32:
            return

        update = 1
        while cond():
            if self.data.standings.is_postseason():
                standings.render_bracket(
                    self.canvas,
                    self.data.config.layout,
                    self.data.config.scoreboard_colors,
                    self.data.standings.leagues[self.standings_league],
                )
            else:
                standings.render_standings(
                    self.canvas,
                    self.data.config.layout,
                    self.data.config.scoreboard_colors,
                    self.data.standings.current_standings(),
                    self.standings_stat,
                )

            if self.data.network_issues:
                network.render_network_error(self.canvas, self.data.config.layout, self.data.config.scoreboard_colors)

            self.canvas = self.matrix.SwapOnVSync(self.canvas)

            if self.data.standings.is_postseason():
                if update % 20 == 0:
                    if self.standings_league == "NL":
                        self.standings_league = "AL"
                    else:
                        self.standings_league = "NL"
            elif self.canvas.width == 32 and update % 5 == 0:
                if self.standings_stat == "w":
                    self.standings_stat = "l"
                else:
                    self.standings_stat = "w"
                    self.data.standings.advance_to_next_standings()
            elif self.canvas.width > 32 and update % 10 == 0:
                self.data.standings.advance_to_next_standings()

            time.sleep(1)
            update = (update + 1) % 100

    def __max_scroll_x(self, scroll_coords):
        scroll_max_x = scroll_coords["x"] + scroll_coords["width"]
        self.scrolling_text_pos = min(scroll_max_x, self.scrolling_text_pos)

    def __update_scrolling_text_pos(self, new_pos, end):
        """Updates the position of scrolling text"""
        pos_after_scroll = self.scrolling_text_pos - 1
        if pos_after_scroll + new_pos < 0:
            self.data.scrolling_finished = True
            if pos_after_scroll + new_pos < -10:
                self.scrolling_text_pos = end
                return
        self.scrolling_text_pos = pos_after_scroll

    def no_games_cond(self) -> bool:
        """A condition that is true only while there are no games live"""
        return not self.data.schedule.games_live()
    
    def __draw_other_sport_game(self):
        """Draw NBA/NHL/NFL/Soccer games."""
        game = self.data.current_other_sport_game
        from data.models.base_game import Sport
        
        if game.sport == Sport.NBA:
            self.__draw_nba_game(game)
        elif game.sport == Sport.NHL:
            self.__draw_nhl_game(game)
        else:
            debug.log(f"Sport {game.sport.value} not yet supported")
            self.canvas.Clear()
            from driver import graphics
            font = graphics.Font()
            font.LoadFont("assets/fonts/patched/4x6.bdf")
            white = graphics.Color(255, 255, 255)
            graphics.DrawText(self.canvas, font, 1, 10, white, f"{game.sport.value}")
            graphics.DrawText(self.canvas, font, 1, 18, white, game.away_team[:10])
            graphics.DrawText(self.canvas, font, 1, 25, white, game.home_team[:10])
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def __draw_nba_game(self, game):
        """Draw NBA game on the LED matrix in a compact, readable format."""
        self.canvas.Clear()
        from driver import graphics
        
        # Load fonts
        font = graphics.Font()
        font.LoadFont("assets/fonts/patched/4x6.bdf")
        
        # Colors
        white = graphics.Color(255, 255, 255)
        red = graphics.Color(255, 0, 0)
        green = graphics.Color(0, 255, 0)
        blue = graphics.Color(100, 100, 255)
        yellow = graphics.Color(255, 255, 0)
        gray = graphics.Color(100, 100, 100)
        
        away_abbrev = self._abbreviate_nba_team(game.away_team)
        home_abbrev = self._abbreviate_nba_team(game.home_team)
        
        if game.is_live():
            # Live game layout - compact and information-dense
            # Row 1: NBA | Period | Time
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NBA")
            period = game.get_period_label()
            graphics.DrawText(self.canvas, font, 22, 6, yellow, period)
            if game.time_remaining:
                time_text = game.time_remaining[:5]  # "12:34" or "0:45"
                graphics.DrawText(self.canvas, font, 40, 6, white, time_text)
            
            # Row 2: Away Team | Score (larger, right-aligned)
            away_color = red if game.away_score > game.home_score else white
            graphics.DrawText(self.canvas, font, 1, 15, away_color, away_abbrev)
            away_score = str(game.away_score)
            score_x = 64 - len(away_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 15, away_color, away_score)
            
            # Row 3: Home Team | Score (larger, right-aligned)
            home_color = red if game.home_score > game.away_score else white
            graphics.DrawText(self.canvas, font, 1, 24, home_color, home_abbrev)
            home_score = str(game.home_score)
            score_x = 64 - len(home_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 24, home_color, home_score)
            
        elif game.is_final():
            # Final game layout
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NBA")
            graphics.DrawText(self.canvas, font, 22, 6, red, "FINAL")
            
            # Determine winner
            away_winner = game.away_score > game.home_score
            home_winner = game.home_score > game.away_score
            
            # Away team
            away_color = green if away_winner else gray
            graphics.DrawText(self.canvas, font, 1, 15, away_color, away_abbrev)
            away_score = str(game.away_score)
            score_x = 64 - len(away_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 15, away_color, away_score)
            
            # Home team
            home_color = green if home_winner else gray
            graphics.DrawText(self.canvas, font, 1, 24, home_color, home_abbrev)
            home_score = str(game.home_score)
            score_x = 64 - len(home_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 24, home_color, home_score)
            
        else:
            # Scheduled/Pregame layout
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NBA")
            
            # Matchup centered
            matchup = f"{away_abbrev} @ {home_abbrev}"
            matchup_x = (64 - len(matchup) * 5) // 2
            graphics.DrawText(self.canvas, font, matchup_x, 15, white, matchup)
            
            # Time (if available)
            if hasattr(game, 'start_time') and game.start_time:
                # Format time nicely (e.g., "7:00 PM" -> "7:00P")
                time_str = str(game.start_time)
                if len(time_str) > 8:
                    # Try to parse datetime
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_str = dt.strftime("%-I:%M%p").replace('M', '')  # "7:00P"
                    except:
                        time_str = time_str[:8]
                
                time_x = (64 - len(time_str) * 5) // 2
                graphics.DrawText(self.canvas, font, time_x, 24, yellow, time_str)
        
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def __draw_nhl_game(self, game):
        """Draw NHL game on the LED matrix in a compact, readable format."""
        self.canvas.Clear()
        from driver import graphics
        
        # Load fonts
        font = graphics.Font()
        font.LoadFont("assets/fonts/patched/4x6.bdf")
        
        # Colors
        white = graphics.Color(255, 255, 255)
        red = graphics.Color(255, 0, 0)
        green = graphics.Color(0, 255, 0)
        blue = graphics.Color(100, 150, 255)
        yellow = graphics.Color(255, 255, 0)
        gray = graphics.Color(100, 100, 100)
        orange = graphics.Color(255, 165, 0)
        
        away_abbrev = self._abbreviate_nhl_team(game.away_team)
        home_abbrev = self._abbreviate_nhl_team(game.home_team)
        
        if game.is_live():
            # Live game layout
            # Row 1: NHL | Period | Time
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NHL")
            period = game.get_period_label()
            
            # Highlight OT/SO in orange
            period_color = orange if (game.is_overtime or game.is_shootout) else yellow
            graphics.DrawText(self.canvas, font, 22, 6, period_color, period)
            
            if game.time_remaining:
                time_text = game.time_remaining[:5]
                graphics.DrawText(self.canvas, font, 40, 6, white, time_text)
            
            # Row 2: Away Team | Score (right-aligned)
            away_color = red if game.away_score > game.home_score else white
            graphics.DrawText(self.canvas, font, 1, 15, away_color, away_abbrev)
            away_score = str(game.away_score)
            score_x = 64 - len(away_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 15, away_color, away_score)
            
            # Row 3: Home Team | Score (right-aligned)
            home_color = red if game.home_score > game.away_score else white
            graphics.DrawText(self.canvas, font, 1, 24, home_color, home_abbrev)
            home_score = str(game.home_score)
            score_x = 64 - len(home_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 24, home_color, home_score)
            
        elif game.is_final():
            # Final game layout
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NHL")
            
            # Show if OT/SO win
            if game.is_shootout:
                graphics.DrawText(self.canvas, font, 22, 6, orange, "FINAL/SO")
            elif game.is_overtime:
                graphics.DrawText(self.canvas, font, 22, 6, orange, "FINAL/OT")
            else:
                graphics.DrawText(self.canvas, font, 22, 6, red, "FINAL")
            
            # Determine winner
            away_winner = game.away_score > game.home_score
            home_winner = game.home_score > game.away_score
            
            # Away team
            away_color = green if away_winner else gray
            graphics.DrawText(self.canvas, font, 1, 15, away_color, away_abbrev)
            away_score = str(game.away_score)
            score_x = 64 - len(away_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 15, away_color, away_score)
            
            # Home team
            home_color = green if home_winner else gray
            graphics.DrawText(self.canvas, font, 1, 24, home_color, home_abbrev)
            home_score = str(game.home_score)
            score_x = 64 - len(home_score) * 5 - 2
            graphics.DrawText(self.canvas, font, score_x, 24, home_color, home_score)
            
        else:
            # Scheduled/Pregame layout
            graphics.DrawText(self.canvas, font, 1, 6, blue, "NHL")
            
            # Matchup centered
            matchup = f"{away_abbrev} @ {home_abbrev}"
            matchup_x = (64 - len(matchup) * 5) // 2
            graphics.DrawText(self.canvas, font, matchup_x, 15, white, matchup)
            
            # Time (if available)
            if hasattr(game, 'start_time') and game.start_time:
                time_str = str(game.start_time)
                if len(time_str) > 8:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_str = dt.strftime("%-I:%M%p").replace('M', '')
                    except:
                        time_str = time_str[:8]
                
                time_x = (64 - len(time_str) * 5) // 2
                graphics.DrawText(self.canvas, font, time_x, 24, yellow, time_str)
        
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
    
    def _abbreviate_nba_team(self, team_name):
        """Abbreviate NBA team names."""
        abbrevs = {
            "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
            "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
            "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
            "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
            "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
            "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
            "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
            "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
            "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
            "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS"
        }
        return abbrevs.get(team_name, team_name[:3].upper())
    
    def _abbreviate_nhl_team(self, team_name):
        """Abbreviate NHL team names."""
        abbrevs = {
            "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
            "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
            "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
            "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
            "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
            "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
            "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
            "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
            "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
            "Toronto Maple Leafs": "TOR", "Vancouver Canucks": "VAN", "Vegas Golden Knights": "VGK",
            "Washington Capitals": "WSH", "Winnipeg Jets": "WPG"
        }
        return abbrevs.get(team_name, team_name[:3].upper())


def permanent_cond() -> bool:
    """A condition that is always true"""
    return True


def timer_cond(seconds) -> Callable[[], bool]:
    """Create a condition that is true for the specified number of seconds"""
    end = time.time() + seconds

    def cond():
        return time.time() < end

    return cond


def all_of(*conds) -> Callable[[], bool]:
    """Create a condition that is true if all of the given conditions are true"""

    def cond():
        return all(c() for c in conds)

    return cond
