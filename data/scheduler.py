"""
Game scheduler that combines games from multiple sports.
Fetches and prioritizes games based on favorite teams and live status.
"""

from typing import List, Optional
from datetime import date, datetime, timezone
from data.models.base_game import BaseGame, GameStatus, Sport
from data.providers.base_provider import BaseProvider

# Adaptive cache TTLs (seconds)
CACHE_TTL_LIVE = 15            # A game is live
CACHE_TTL_PREGAME_SOON = 120   # Next game starts within 15 min
CACHE_TTL_IDLE = 30 * 60       # No games soon


class GameScheduler:
    """
    Centralized scheduler for multi-sport games.
    Combines games from multiple providers and prioritizes them.
    """

    def __init__(self, providers: List[BaseProvider], favorite_team_ids: Optional[dict] = None):
        """
        Initialize the game scheduler.

        Args:
            providers: List of sport providers (MLB, NBA, NHL, etc.)
            favorite_team_ids: Dict mapping Sport -> List of team IDs
                Example: {Sport.NBA: ["134871"], Sport.MLB: ["147"]}
        """
        self.providers = providers
        self.favorite_team_ids = favorite_team_ids or {}
        self._cache = {}
        self._cache_time = None

    def _cache_ttl(self, games: List[BaseGame]) -> int:
        """Return a cache TTL appropriate for the current game state."""
        now = datetime.now(timezone.utc)
        any_live = False
        soonest_sec = None

        for game in games:
            if game.status == GameStatus.LIVE:
                any_live = True
                break
            if game.status == GameStatus.SCHEDULED and game.start_time:
                try:
                    start = game.start_time
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=timezone.utc)
                    delta = (start - now).total_seconds()
                    if delta > 0 and (soonest_sec is None or delta < soonest_sec):
                        soonest_sec = delta
                except Exception:
                    pass

        if any_live:
            return CACHE_TTL_LIVE
        if soonest_sec is not None and soonest_sec <= 15 * 60:
            return CACHE_TTL_PREGAME_SOON
        return CACHE_TTL_IDLE

    def get_todays_games(self, refresh: bool = False) -> List[BaseGame]:
        """
        Get all games for today across all sports.

        Args:
            refresh: Force refresh from APIs (ignore cache)

        Returns:
            List of BaseGame objects sorted by priority
        """
        today = date.today()
        cache_key = f"games_{today}"

        # Check cache – TTL adapts to whether games are live / upcoming
        if not refresh and cache_key in self._cache:
            if self._cache_time:
                age = (datetime.now() - self._cache_time).total_seconds()
                ttl = self._cache_ttl(self._cache[cache_key])
                if age < ttl:
                    return self._cache[cache_key]

        # Fetch games from all providers
        all_games = []
        for provider in self.providers:
            sport = provider.get_sport()
            team_ids = self.favorite_team_ids.get(sport)

            try:
                games = provider.get_games_for_date(today, team_ids)
                all_games.extend(games)
            except Exception as e:
                print(f"Error fetching {sport.value} games: {e}")

        # Sort by priority
        sorted_games = self._prioritize_games(all_games)

        # Update cache
        self._cache[cache_key] = sorted_games
        self._cache_time = datetime.now()

        return sorted_games

    def get_live_games(self) -> List[BaseGame]:
        """Get all currently live games across all sports."""
        all_games = self.get_todays_games()
        return [game for game in all_games if game.is_live()]

    def _prioritize_games(self, games: List[BaseGame]) -> List[BaseGame]:
        """
        Sort games by priority.
        Priority order: Live > Scheduled (by start time) > Final
        """
        def priority_key(game: BaseGame):
            # Live games first (lowest number = highest priority)
            if game.status == GameStatus.LIVE:
                return (0, game.start_time or datetime.min)
            # Scheduled games next, sorted by start time
            elif game.status == GameStatus.SCHEDULED:
                return (1, game.start_time or datetime.max)
            # Final games last
            else:
                return (2, game.start_time or datetime.max)

        return sorted(games, key=priority_key)

    def clear_cache(self):
        """Clear the game cache."""
        self._cache = {}
        self._cache_time = None
