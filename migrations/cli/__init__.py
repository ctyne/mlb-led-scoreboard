import argparse

from migrations.cli.up import Up
from migrations.cli.down import Down
from migrations.cli.generate import Generate


def positive_int(value):
    """Custom argparse type for positive integers."""
    ivalue = int(value)

    if ivalue < 1:
        raise argparse.ArgumentTypeError("must be at least 1")

    return ivalue

class CLI:
    COMMANDS = {
        "generate": Generate,
        "g": Generate,
        "up": Up,
        "u": Up,
        "down": Down,
        "d": Down
    }

    @staticmethod
    def execute():
        parser = argparse.ArgumentParser(description="Data migration manager for mlb-led-scoreboard configuration objects.")
        subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

        # "generate" command
        generate_parser = subparsers.add_parser('generate', help='Generate a new migration file')
        generate_parser.add_argument('migration_name', type=str, help='Name of the migration')

        # "up" command
        up_parser = subparsers.add_parser('up', help='Run migrations')
        up_parser.add_argument(
            '--step',
            type=positive_int,
            default=999_999,
            help='Number of migrations to process (defaults to all migrations)'
        )

        # "down" command
        down_parser = subparsers.add_parser('down', help='Roll back migrations')
        down_parser.add_argument(
            '--step',
            type=positive_int,
            default=1,
            help='Number of migrations to process (defaults to most recent)'
        )

        args = parser.parse_args()

        if args.command not in CLI.COMMANDS:
            # TODO
            raise

        cmd = CLI.COMMANDS[args.command]
        cmd(args).execute()
