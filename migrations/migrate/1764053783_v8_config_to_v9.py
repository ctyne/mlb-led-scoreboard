from migrations import *


TARGET = BASE_PATH / "config.schema.json"

class v8_config_to_v9(ConfigMigration):
    def up(self, txn, ctx):
        for config in configs(TARGET, ctx=ctx):
            with txn.load_for_update(config) as content:
                # pregame_weather -> weather.pregame
                pregame_weather = content["pregame_weather"]
                del content["pregame_weather"]
                content["weather"]["pregame"] = pregame_weather

                # delete name configs
                del content["full_team_names"]
                del content["short_team_names_for_runs_hits"]

                # Calculate the correct 'sync_delay_seconds' based on API refresh and deprecated game delay multiplier
                api_refresh_rate = content["api_refresh_rate"]
                delay_multiplier = content["preferred_game_delay_multiplier"]

                content["sync_delay_seconds"] = api_refresh_rate * delay_multiplier

                del content["preferred_game_delay_multiplier"]

    def down(self, txn, ctx):
        # up() deletes keys, so is irreversible
        raise IrreversibleMigration
