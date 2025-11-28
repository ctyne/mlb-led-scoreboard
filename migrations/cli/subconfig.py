import os, pathlib, shutil

from migrations.cli.command import CLICommand
from migrations.manager import MigrationManager
from migrations.status import MigrationStatus
from migrations.transaction import Transaction


class Subconfig(CLICommand):
    """
    Creates a subconfiguration from a known configuration reference.
    If not instantiated with a reference, it can be inferred from the name of the subconfiguration.

    Subconfigurations are expected to match the structure correctly:

        <name>.<subname>.json
            references
        <name>.json
            which has schema
        <name>.schema.json
    """

    def __init__(self, arguments) -> None:
        self.subconfig = pathlib.Path(arguments.subconfig)
        self.reference = (
            pathlib.Path(arguments.reference) if arguments.reference else Subconfig.infer_reference(self.subconfig)
        )
        self.schema = self.reference.with_suffix("").with_suffix(".schema.json")

    def execute(self) -> None:
        print(f"Initializing subconfig...")

        validation_error = self.validate_paths()
        if validation_error:
            print(validation_error)
            print("Aborting...")
            return
        else:
            print(f"\tSubconfig name `{self.subconfig}` is valid.")
            print(f"\tLocated reference `{self.reference}`.")
            print(f"\tLocated schema '{self.schema}'.")

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

    def validate_paths(self) -> str | None:
        """
        Validates that the subconfig correctly references a known configuration and schema.

        Returns an error string if not valid.
        """
        if not self.subconfig.name.count(".") == 2:
            return f"Expected 3 part subconfig in format '<name>.<subname>.json', got: {self.subconfig}"

        name, _subname, _ext = self.subconfig.name.split(".")

        expected_reference = name + ".json"
        expected_schema = name + ".schema.json"

        if not self.reference.name == expected_reference and os.path.exists(self.reference):
            return f"Subconfig does not reference a known config! Expected reference '{expected_reference}' to exist."

        if not self.schema.name == expected_schema and os.path.exists(self.schema):
            return f"Subconfig does not reference a known schema! Expected schema '{expected_schema}' to exist."

    @staticmethod
    def infer_reference(subconfig: pathlib.Path) -> pathlib.Path:
        suffix = subconfig.suffix

        while "." in subconfig.name:
            subconfig = subconfig.with_suffix("")

        return subconfig.with_suffix(suffix)
