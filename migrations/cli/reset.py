import os, pathlib

from migrations.cli.command import CLICommand
from migrations.status import MigrationStatus
from migrations.manager import MigrationManager


class Reset(CLICommand):
    def __init__(self, arguments) -> None:
        self.force = arguments.force

    def execute(self) -> None:
        """
        Removes custom configurations and resets (destroys) the custom status migration checkpoint.
        The migration system must be reinitialized via Init.

        This does NOT alter schema migrations!
        """
        print(
            "WARNING! Resetting migrations is a destructive action and removes any custom configurations you might have."
        )
        print("\tYou will need to reinitialize the migrations via 'migrations init' before use.")

        if not self.force:
            answer = input("Are you sure you want to continue? (y/n)")

            if answer not in "Yy":
                print("Aborting...")
                return

        project_root = pathlib.Path(__file__).parent.parent.parent
        search_dirs = [project_root, project_root / "coordinates", project_root / "colors"]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            schemas = list(search_dir.glob("*.schema.json"))
            for file in search_dir.glob("*.json"):
                if MigrationManager.is_schema(file):
                    continue

                removable = False

                for schema in schemas:
                    if file.with_suffix("") == schema.with_suffix("").with_suffix(""):
                        removable = True

                if removable:
                    print(f"\tRemoving {file}")
                    os.remove(file)

        if MigrationStatus.CUSTOM_STATUS_FILE.exists():
            print(f"\tRemoving {MigrationStatus.CUSTOM_STATUS_FILE}")
            os.remove(MigrationStatus.CUSTOM_STATUS_FILE)

        print("Done.")
