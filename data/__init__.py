import time
from data.screens import ScreenType

import debug
from data import status
from data.game import Game
from data.headlines import Headlines
from data.schedule import Schedule
from data.scoreboard import Scoreboard
from data.scoreboard.postgame import Postgame
from data.scoreboard.pregame import Pregame
from data.standings import Standings
from data.update import UpdateStatus
from data.weather import Weather
from data.multi_sport import MultiSportData
from data.models.base_game import GameStatus

class Data:
    def __init__(self, config):
        # Save the parsed config
        self.config = config

        # Initialize multi-sport support FIRST
        self.multi_sport = MultiSportData(config)
        self.current_game_is_other_sport = False
        self.current_other_sport_game = None
        self.other_sport_games = []
        self.combined_game_index = 0  # Track position across ALL games
        self.last_other_sport_refresh = 0  # Track last refresh time for rate limiting

        # get MLB schedule
        self.schedule: Schedule = Schedule(config)
        # NB: Can return none, but shouldn't matter?
        self.current_game: Game = self.schedule.get_preferred_game()

        # Fetch other sport games if enabled
        if self.multi_sport.enabled:
            try:
                self.other_sport_games = self.multi_sport.get_todays_games()
                debug.log(f"Found {len(self.other_sport_games)} other sport games")
                
                # Set initial game based on priority (live > scheduled > final)
                if self.other_sport_games:
                    # Check if there are any live games in other sports
                    live_other_games = [g for g in self.other_sport_games if g.is_live()]
                    
                    if live_other_games:
                        # Start with first live other sport game
                        self.current_game_is_other_sport = True
                        self.current_other_sport_game = live_other_games[0]
                        self.current_game = None
                        self.combined_game_index = 0
                        debug.log(f"Starting with live {live_other_games[0].sport.value} game")
            except Exception as e:
                debug.log(f"Error fetching other sport games: {e}")
                self.other_sport_games = []

        self.game_changed_time = time.time()
        if self.current_game is not None:
            self.print_game_data_debug()
            self.__update_layout_state()

        # Weather info
        self.weather: Weather = Weather(config)

        # News headlines
        self.headlines: Headlines = Headlines(config, self.schedule.date.year)

        # Fetch all standings data for today
        self.standings: Standings = Standings(config, self.headlines.important_dates.playoffs_start_date)

        # Network status state - we useweather condition as a sort of sentinial value
        self.network_issues: bool = self.weather.conditions == "Error"

        # RENDER ITEMS
        self.scrolling_finished: bool = False

    def should_rotate_to_next_game(self):
        if not self.config.rotation_enabled:
            # never rotate
            return False

        if self.config.rotation_preferred_team_live_enabled or not self.config.preferred_teams:
            # if there's no preferred team, or if we rotate during their games, always rotate
            return True

        game = self.current_game

        if status.is_live(game.status()):
            if self.schedule.num_games() <= 1:
                # don't rotate if this is the only game
                return False

            # if we're here, it means we should pause on the preferred team's games
            if game.features_team(self.config.preferred_teams[0]):
                # unless we're allowed to rotate during mid-inning breaks
                return self.config.rotation_preferred_team_live_mid_inning and status.is_inning_break(game.inning_state())

        # if our current game isn't live, we might as well try to rotate.
        # this should help most issues with games getting stuck
        return True

    def refresh_game(self):
        """Refresh current game data."""
        if self.current_game_is_other_sport:
            # For other sports, we refresh all games and update the current one
            self.refresh_other_sports()
            # Note: Other sport games are already live-updated from ESPN
            # No individual game update needed like MLB's statsapi
            return
        
        # MLB game refresh
        status = self.current_game.update()
        if status == UpdateStatus.SUCCESS:
            self.__update_layout_state()
            self.print_game_data_debug()
            self.network_issues = False
        elif status == UpdateStatus.FAIL:
            self.network_issues = True


    def advance_to_next_game(self):
        """Advance to the next game in rotation (MLB or other sports)."""
        if self.multi_sport.enabled and self.other_sport_games:
            # Create combined list of all games
            # Access schedule's internal _games list directly
            mlb_scheduled_games = getattr(self.schedule, '_games', [])
            
            # Convert MLB scheduled games to Game objects to check status
            mlb_game_objects = []
            for scheduled_game in mlb_scheduled_games:
                game = Game.from_scheduled(scheduled_game, self.config.preferred_game_delay_multiplier, self.config.api_refresh_rate)
                if game:
                    mlb_game_objects.append((scheduled_game, game))
            
            # Categorize ALL games (MLB + other sports) by status
            all_live = []
            all_scheduled = []
            all_final = []
            
            # Categorize MLB games
            for scheduled_game, game in mlb_game_objects:
                game_status = game.status()
                if game_status == status.IN_PROGRESS or game_status == status.DELAYED:
                    all_live.append(('mlb', scheduled_game))
                elif game_status == status.SCHEDULED or game_status == status.WARMUP or game_status == status.PRE_GAME:
                    all_scheduled.append(('mlb', scheduled_game))
                elif game_status == status.FINAL:
                    all_final.append(('mlb', scheduled_game))
            
            # Categorize other sport games
            for game in self.other_sport_games:
                if game.is_live():
                    all_live.append(('other', game))
                elif game.status == GameStatus.SCHEDULED:
                    all_scheduled.append(('other', game))
                elif game.is_final():
                    all_final.append(('other', game))
            
            # Determine which games to show based on priority
            if all_live:
                active_games = all_live
            elif all_scheduled:
                active_games = all_scheduled
            else:
                active_games = all_final
            
            if len(active_games) == 0:
                debug.warning("No games available (MLB or other sports)")
                self.network_issues = True
                return
            
            # Move to next game in rotation
            self.combined_game_index = (self.combined_game_index + 1) % len(active_games)
            
            # Get the game at this index
            game_type, game_data = active_games[self.combined_game_index]
            
            if game_type == 'mlb':
                # It's an MLB game
                self.current_game_is_other_sport = False
                self.current_other_sport_game = None
                game = Game.from_scheduled(game_data, self.config.preferred_game_delay_multiplier, self.config.api_refresh_rate)
                
                if game:
                    self.current_game = game
                    self.game_changed_time = time.time()
                    self.__update_layout_state()
                    self.print_game_data_debug()
                    self.network_issues = False
                else:
                    debug.warning(f"Failed to create Game object at index {self.combined_game_index}")
            else:
                # It's an other sport game
                self.current_game_is_other_sport = True
                self.current_other_sport_game = game_data
                self.current_game = None  # Clear MLB game
                self.game_changed_time = time.time()
                self.scrolling_finished = False
                debug.log(f"Switching to {self.current_other_sport_game.sport.value} game: {self.current_other_sport_game.away_team} @ {self.current_other_sport_game.home_team}")
        else:
            # Original MLB-only behavior
            game = self.schedule.next_game()
            if game is None:
                self.network_issues = True
                return

            if game.game_id != self.current_game.game_id:
                self.current_game = game
                self.game_changed_time = time.time()
                self.__update_layout_state()
                self.print_game_data_debug()
                self.network_issues = False

            elif self.current_game is not None:
                # prefer to update the existing game rather than
                # rotating if its the same game.
                # this helps with e.g. the delay logic
                debug.log("Rotating to the same game, refreshing instead")
                self.refresh_game()

    def refresh_other_sports(self):
        """Refresh other sport games data (rate limited to every 15 seconds)."""
        if not self.multi_sport.enabled:
            return
        
        # Rate limit: only refresh every 15 seconds
        current_time = time.time()
        if current_time - self.last_other_sport_refresh < 15:
            return
        
        self.last_other_sport_refresh = current_time
        debug.log("Refreshing other sport games...")
        
        try:
            # Refresh games from ESPN API (ignores 5-min cache)
            self.other_sport_games = self.multi_sport.get_todays_games(refresh=True)
            debug.log(f"Refreshed {len(self.other_sport_games)} other sport games")
            
            # Update the current game if it's in the refreshed list
            if self.current_other_sport_game:
                current_id = self.current_other_sport_game.game_id
                for game in self.other_sport_games:
                    if game.game_id == current_id:
                        old_score = f"{self.current_other_sport_game.away_score}-{self.current_other_sport_game.home_score}"
                        new_score = f"{game.away_score}-{game.home_score}"
                        self.current_other_sport_game = game
                        debug.log(f"Updated current game: {game.away_team} @ {game.home_team} ({old_score} -> {new_score})")
                        break
        except Exception as e:
            debug.log(f"Error refreshing other sport games: {e}")

    def refresh_standings(self):
        self.__process_network_status(self.standings.update())

    def refresh_weather(self):
        self.__process_network_status(self.weather.update())

    def refresh_news_ticker(self):
        self.__process_network_status(self.headlines.update())

    def refresh_schedule(self, force=False):
        self.__process_network_status(self.schedule.update(force))
        
        # Also refresh other sports if enabled
        if self.multi_sport.enabled:
            try:
                self.other_sport_games = self.multi_sport.get_todays_games()
                debug.log(f"Refreshed: {len(self.other_sport_games)} other sport games")
            except Exception as e:
                debug.log(f"Error refreshing other sport games: {e}")

    def __process_network_status(self, status):
        if status == UpdateStatus.SUCCESS:
            self.network_issues = False
        elif status == UpdateStatus.FAIL:
            self.network_issues = True

    def get_screen_type(self) -> ScreenType:
        # Always the news
        if self.config.news_ticker_always_display:
            return ScreenType.ALWAYS_NEWS
        # Always the standings
        if self.config.standings_always_display:
            return ScreenType.ALWAYS_STANDINGS
        # Full MLB Offday
        if self.schedule.is_offday():
            return ScreenType.LEAGUE_OFFDAY

        # Preferred Team Offday
        if self.schedule.is_offday_for_preferred_team() and (
            self.config.news_ticker_team_offday or self.config.standings_team_offday
        ):
            return ScreenType.PREFERRED_TEAM_OFFDAY

        # Playball!
        return ScreenType.GAMEDAY

    def __update_layout_state(self):
        import data.config.layout as layout

        self.config.layout.set_state()
        if self.current_game.status() == status.WARMUP:
            self.config.layout.set_state(layout.LAYOUT_STATE_WARMUP)

        if self.current_game.is_no_hitter():
            self.config.layout.set_state(layout.LAYOUT_STATE_NOHIT)

        if self.current_game.is_perfect_game():
            self.config.layout.set_state(layout.LAYOUT_STATE_PERFECT)

    def print_game_data_debug(self):
        debug.log("Game Data Refreshed: %s", self.current_game._current_data["gameData"]["game"]["id"])
        debug.log("Current game is %d seconds behind", self.current_game.current_delay())
        debug.log("Pre: %s", Pregame(self.current_game, self.config.time_format))
        debug.log("Live: %s", Scoreboard(self.current_game))
        debug.log("Final: %s", Postgame(self.current_game))
