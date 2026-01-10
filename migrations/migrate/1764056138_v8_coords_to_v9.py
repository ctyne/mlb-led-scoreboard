from migrations import *


W32H32 = COORDINATES_PATH / "w32h32.schema.json"
W64H32 = COORDINATES_PATH / "w64h32.schema.json"
W64H64 = COORDINATES_PATH / "w64h64.schema.json"
W128H32 = COORDINATES_PATH / "w128h32.schema.json"
W128H64 = COORDINATES_PATH / "w128h64.schema.json"
W192H64 = COORDINATES_PATH / "w192h64.schema.json"

ALL_COORDS = [W32H32, W64H32, W64H64, W128H32, W128H64, W192H64]


class v8_coords_to_v9(ConfigMigration):
    def up(self, ctx: MigrationContext):
        # Add teams.name.full default
        ctx.add_key(W32H32, "teams.name.full", False)
        ctx.add_key(W64H32, "teams.name.full", True)
        ctx.add_key(W64H64, "teams.name.full", True)
        ctx.add_key(W128H32, "teams.name.full", True)
        ctx.add_key(W128H64, "teams.name.full", True)
        ctx.add_key(W192H64, "teams.name.full", True)

        # Add teams.name.shorten_on_high_line_score default
        ctx.add_key(W32H32, "teams.name.shorten_on_high_line_score", True)
        ctx.add_key(W64H32, "teams.name.shorten_on_high_line_score", True)
        ctx.add_key(W64H64, "teams.name.shorten_on_high_line_score", True)
        ctx.add_key(W128H32, "teams.name.shorten_on_high_line_score", True)
        ctx.add_key(W128H64, "teams.name.shorten_on_high_line_score", True)
        ctx.add_key(W192H64, "teams.name.shorten_on_high_line_score", True)

        # Move teams.runs to teams.line_score
        ctx.rename_key(W32H32, "teams.runs", "line_score")
        ctx.rename_key(W64H32, "teams.runs", "line_score")
        ctx.rename_key(W64H64, "teams.runs", "line_score")
        ctx.rename_key(W128H32, "teams.runs", "line_score")
        ctx.rename_key(W128H64, "teams.runs", "line_score")
        ctx.rename_key(W192H64, "teams.runs", "line_score")

        # Swap the line score structure
        for config in ctx.configs(ALL_COORDS):
            with ctx.load_for_update(config) as content:
                line_score = content["teams"]["line_score"]

                rhe = line_score["runs_hits_errors"]

                # Unpack runs_hits_errors to top-level line_score
                # Move run_hits_errors.show -> show_hits_and_errors
                line_score = line_score | {
                    "show_hits_and_errors": rhe["show"],
                    "compress_digits": rhe["compress_digits"],
                    "spacing": rhe["spacing"],
                }

                content["teams"]["line_score"] = line_score

                del content["teams"]["line_score"]["runs_hits_errors"]

    def down(self, ctx: MigrationContext):
        # Remove standings.team.name.full default
        ctx.remove_key(W32H32, "teams.name.full")
        ctx.remove_key(W64H32, "teams.name.full")
        ctx.remove_key(W64H64, "teams.name.full")
        ctx.remove_key(W128H32, "teams.name.full")
        ctx.remove_key(W128H64, "teams.name.full")
        ctx.remove_key(W192H64, "teams.name.full")

        # Remove standings.team.name.shorten_on_high_line_score default
        ctx.remove_key(W32H32, "teams.name.shorten_on_high_line_score")
        ctx.remove_key(W64H32, "teams.name.shorten_on_high_line_score")
        ctx.remove_key(W64H64, "teams.name.shorten_on_high_line_score")
        ctx.remove_key(W128H32, "teams.name.shorten_on_high_line_score")
        ctx.remove_key(W128H64, "teams.name.shorten_on_high_line_score")
        ctx.remove_key(W192H64, "teams.name.shorten_on_high_line_score")

        # Move teams.line_score to teams.runs
        ctx.rename_key(W32H32, "teams.line_score", "runs")
        ctx.rename_key(W64H32, "teams.line_score", "runs")
        ctx.rename_key(W64H64, "teams.line_score", "runs")
        ctx.rename_key(W128H32, "teams.line_score", "runs")
        ctx.rename_key(W128H64, "teams.line_score", "runs")
        ctx.rename_key(W192H64, "teams.line_score", "runs")

        # Swap the line score structure
        for config in ctx.configs(ALL_COORDS):
            with ctx.load_for_update(config) as content:
                runs = content["teams"]["runs"]

                rhe = {
                    "show": runs["show_hits_and_errors"],
                    "compress_digits": runs["compress_digits"],
                    "spacing": runs["spacing"],
                }

                content["teams"]["runs"]["runs_hits_errors"] = rhe

                del content["teams"]["runs"]["show_hits_and_errors"]
                del content["teams"]["runs"]["compress_digits"]
                del content["teams"]["runs"]["spacing"]
