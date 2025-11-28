from migrations import *


W32H32 = COORDINATES_PATH / "w32h32.schema.json"
W64H32 = COORDINATES_PATH / "w64h32.schema.json"
W64H64 = COORDINATES_PATH / "w64h64.schema.json"
W128H32 = COORDINATES_PATH / "w128h32.schema.json"
W128H64 = COORDINATES_PATH / "w128h64.schema.json"
W192H64 = COORDINATES_PATH / "w192h64.schema.json"

ALL_COORDS = [W32H32, W64H32, W64H64, W128H32, W128H64, W192H64]

class v8_coords_to_v9(ConfigMigration):
    def up(self, txn, ctx):
        # Add teams.name.full default
        add_key(txn, W32H32, "teams.name.full", False, ctx=ctx)
        add_key(txn, W64H32, "teams.name.full", True, ctx=ctx)
        add_key(txn, W64H64, "teams.name.full", True, ctx=ctx)
        add_key(txn, W128H32, "teams.name.full", True, ctx=ctx)
        add_key(txn, W128H64, "teams.name.full", True, ctx=ctx)
        add_key(txn, W192H64, "teams.name.full", True, ctx=ctx)

        # Add teams.name.shorten_on_high_line_score default
        add_key(txn, W32H32, "teams.name.shorten_on_high_line_score", True, ctx=ctx)
        add_key(txn, W64H32, "teams.name.shorten_on_high_line_score", True, ctx=ctx)
        add_key(txn, W64H64, "teams.name.shorten_on_high_line_score", True, ctx=ctx)
        add_key(txn, W128H32, "teams.name.shorten_on_high_line_score", True, ctx=ctx)
        add_key(txn, W128H64, "teams.name.shorten_on_high_line_score", True, ctx=ctx)
        add_key(txn, W192H64, "teams.name.shorten_on_high_line_score", True, ctx=ctx)

        # Move teams.runs to teams.line_score
        rename_key(txn, W32H32, "teams.runs", "line_score", ctx=ctx)
        rename_key(txn, W64H32, "teams.runs", "line_score", ctx=ctx)
        rename_key(txn, W64H64, "teams.runs", "line_score", ctx=ctx)
        rename_key(txn, W128H32, "teams.runs", "line_score", ctx=ctx)
        rename_key(txn, W128H64, "teams.runs", "line_score", ctx=ctx)
        rename_key(txn, W192H64, "teams.runs", "line_score", ctx=ctx)

        # Swap the line score structure
        for config in configs(ALL_COORDS, ctx=ctx):
            with txn.load_for_update(config) as content:
                line_score = content["teams"]["line_score"]

                rhe = line_score["runs_hits_errors"]
                
                # Unpack runs_hits_errors to top-level line_score
                # Move run_hits_errors.show -> show_hits_and_errors
                line_score = line_score | {
                    "show_hits_and_errors": rhe["show"],
                    "compress_digits": rhe["compress_digits"],
                    "spacing": rhe["spacing"]
                }

                content["teams"]["line_score"] = line_score

                del content["teams"]["line_score"]["runs_hits_errors"]

    def down(self, txn, ctx):
        # Remove standings.team.name.full default
        remove_key(txn, W32H32, "teams.name.full", ctx=ctx)
        remove_key(txn, W64H32, "teams.name.full", ctx=ctx)
        remove_key(txn, W64H64, "teams.name.full", ctx=ctx)
        remove_key(txn, W128H32, "teams.name.full", ctx=ctx)
        remove_key(txn, W128H64, "teams.name.full", ctx=ctx)
        remove_key(txn, W192H64, "teams.name.full", ctx=ctx)

        # Remove standings.team.name.shorten_on_high_line_score default
        remove_key(txn, W32H32, "teams.name.shorten_on_high_line_score", ctx=ctx)
        remove_key(txn, W64H32, "teams.name.shorten_on_high_line_score", ctx=ctx)
        remove_key(txn, W64H64, "teams.name.shorten_on_high_line_score", ctx=ctx)
        remove_key(txn, W128H32, "teams.name.shorten_on_high_line_score", ctx=ctx)
        remove_key(txn, W128H64, "teams.name.shorten_on_high_line_score", ctx=ctx)
        remove_key(txn, W192H64, "teams.name.shorten_on_high_line_score", ctx=ctx)

        # Move teams.line_score to teams.runs
        rename_key(txn, W32H32, "teams.line_score", "runs", ctx=ctx)
        rename_key(txn, W64H32, "teams.line_score", "runs", ctx=ctx)
        rename_key(txn, W64H64, "teams.line_score", "runs", ctx=ctx)
        rename_key(txn, W128H32, "teams.line_score", "runs", ctx=ctx)
        rename_key(txn, W128H64, "teams.line_score", "runs", ctx=ctx)
        rename_key(txn, W192H64, "teams.line_score", "runs", ctx=ctx)

        # Swap the line score structure
        for config in configs(ALL_COORDS, ctx=ctx):
            with txn.load_for_update(config) as content:
                runs = content["teams"]["runs"]

                rhe = {
                    "show": runs["show_hits_and_errors"],
                    "compress_digits": runs["compress_digits"],
                    "spacing": runs["spacing"]
                }

                content["teams"]["runs"]["runs_hits_errors"] = rhe

                del content["teams"]["runs"]["show_hits_and_errors"]
                del content["teams"]["runs"]["compress_digits"]
                del content["teams"]["runs"]["spacing"]
