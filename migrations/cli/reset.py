import os, pathlib

from migrations.cli.command import CLICommand
from migrations.manager import MigrationManager
from migrations.status import MigrationStatus
from migrations.transaction import Transaction


class Reset(CLICommand):
    def __init__(self, _arguments):
        pass

    def execute(self):
        """
        Removes custom configurations and resets (destroys) the custom status migration checkpoint.
        The migration system must be reinitialized via Init.

        This does NOT alter schema migrations!
        """
        print("WARNING! Resetting migrations is a destructive action and removes any custom configurations you might have.")
        print("\tYou will need to reinitialize the migrations via 'migrations init' before use.")
        answer = input("Are you sure you want to continue? (y/n)")

        if answer not in "Yy":
            print("Aborting...")
            return

        print("=" * 80)

        project_root = pathlib.Path(__file__).parent.parent.parent
        search_dirs = [project_root, project_root / "coordinates", project_root / "colors"]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for schema_file in search_dir.glob("*.schema.json"):
                target_file = schema_file.with_suffix("").with_suffix(".json")

                if target_file.exists():
                    print(f"\tRemoving {target_file}")
                    os.remove(target_file)

        print(f"\tRemoving {MigrationStatus.CUSTOM_STATUS_FILE}")
        os.remove(MigrationStatus.CUSTOM_STATUS_FILE)

        print("=" * 80)
