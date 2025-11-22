import json, os, pathlib, shutil

from migrations.cli.command import CLICommand
from migrations.manager import MigrationManager
from migrations.status import MigrationStatus
from migrations.transaction import Transaction


class Subconfig(CLICommand):
    def __init__(self, arguments):
        self.subconfig = pathlib.Path(arguments.subconfig)
        self.reference = pathlib.Path(arguments.reference) if arguments.reference else Subconfig.infer_reference(self.subconfig)

    def execute(self):
        print(f"Initializing subconfig {self.subconfig} using reference {self.reference}...")

        if not os.path.exists(self.reference):
            print("Reference does not exist! Aborting...")

        already_exists = os.path.exists(self.subconfig)
        subconfig_migrations = MigrationStatus.get_migrations(self.subconfig)
        reference_migrations = MigrationStatus.get_migrations(self.reference)
        versions_match = subconfig_migrations == reference_migrations
        
        if already_exists:
            print("\tSubconfig already exists, skipping file creation.")

            if not versions_match:
                print("\tSubconfig and reference migration versions don't match! Remove the subconfig, then try again.")
                print("Aborting...")

                return
        else:
            shutil.copy2(self.reference, self.subconfig)

        print("\tWriting migration status...\n")

        with Transaction() as txn:
            with txn.load_for_update(MigrationStatus.CUSTOM_STATUS_FILE) as custom_status:
                custom_status[MigrationManager.normalize_path(self.subconfig)] = reference_migrations

        print("Done.")

    @staticmethod
    def infer_reference(subconfig: pathlib.Path) -> pathlib.Path:
        suffix = subconfig.suffix

        while "." in subconfig.name:
            subconfig = subconfig.with_suffix("")

        return subconfig.with_suffix(suffix)
