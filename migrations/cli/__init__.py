import argparse, os

from migrations.cli.up import Up
from migrations.cli.down import Down
from migrations.cli.generate import Generate
from migrations.cli.init import Init
from migrations.cli.subconfig import Subconfig
from migrations.cli.reset import Reset


def positive_int(value) -> int:
    """Custom argparse type for positive integers."""
    ivalue = int(value)

    if ivalue < 1:
        raise argparse.ArgumentTypeError("must be at least 1")

    return ivalue


class CLI:
    COMMANDS = {
        # Full commands
        "generate": Generate,
        "up": Up,
        "down": Down,
        "init": Init,
        "subconfig": Subconfig,
        "reset": Reset,
        # Aliases
        "g": Generate,
        "u": Up,
        "d": Down,
        "i": Init,
        "s": Subconfig,
        "r": Reset,
    }

    @staticmethod
    def execute() -> None:
        parser = argparse.ArgumentParser(
            description="Data migration manager for mlb-led-scoreboard configuration objects."
        )
        subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

        # "init" command
        subparsers.add_parser("init", aliases=["i"], help="Initialize config files from schemas")

        # "reset" command
        reset_parser = subparsers.add_parser(
            "reset", aliases=["r"], help="Resets custom migrations, preserving schemas"
        )
        reset_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation and force reset")

        # "subconfig" command
        subconfig_parser = subparsers.add_parser(
            "subconfig",
            aliases=["s"],
            help="Create a subconfiguration from a reference that inherits the migration state of the reference",
        )
        subconfig_parser.add_argument("subconfig", type=str, help="Relative path of the subconfig")
        subconfig_parser.add_argument(
            "-r",
            "--reference",
            type=str,
            help="Relative path of the reference. If not present, will be inferred from the subconfig path",
            required=False,
        )

        # "generate" command
        generate_parser = subparsers.add_parser("generate", aliases=["g"], help="Generate a new migration file")
        generate_parser.add_argument("migration_name", type=str, help="Name of the migration")

        # "up" command
        up_parser = subparsers.add_parser("up", aliases=["u"], help="Run migrations")
        up_parser.add_argument(
            "-s",
            "--step",
            type=positive_int,
            default=999_999,
            help="Number of migrations to process (defaults to all migrations)",
        )

        # "down" command
        down_parser = subparsers.add_parser("down", aliases=["d"], help="Roll back migrations")
        down_parser.add_argument(
            "-s",
            "--step",
            type=positive_int,
            default=1,
            help="Number of migrations to process (defaults to most recent)",
        )

        args = parser.parse_args()

        if args.command not in CLI.COMMANDS:
            print(f"\nError: Unknown command '{args.command}'")
            exit(1)

        # Check if migration system is initialized (except for init/reset commands)
        if args.command not in ["init", "i", "reset", "r"]:
            CLI.require_initialization()

        cmd = CLI.COMMANDS[args.command]
        cmd(args).execute()

    @staticmethod
    def require_initialization() -> None:
        """Ensure the migration system has been initialized before running commands."""
        from migrations.status import MigrationStatus

        if not os.path.exists(MigrationStatus.CUSTOM_STATUS_FILE):
            print(
                """\
Error: Migration system is not initialized yet.

Please run the following command first:
  python -m migrations init
"""
            )
            exit(1)
