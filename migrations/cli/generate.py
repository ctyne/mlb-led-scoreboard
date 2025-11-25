import time

from migrations.cli.command import CLICommand
from migrations.manager import MIGRATIONS_PATH


MIGRATION_TEMPLATE = """\
from migrations import *


class {}(ConfigMigration):
    def up(self, txn):
        raise NotImplementedError("Migration logic not implemented.")

    def down(self, txn):
        # Implement the logic to revert the migration if necessary.
        # Raises IrreversibleMigration by default.
        raise IrreversibleMigration
"""


class Generate(CLICommand):
    """
    Generates a new migration from the template, with the version set to the current UTC timestamp.
    """
    def __init__(self, arguments):
        self.__validate_migration_name(arguments.migration_name)
        self.migration_name = arguments.migration_name

    def execute(self):
        print(f"Generating migration '{self.migration_name}'.")

        ts = int(time.time())
        filename = f"{ts}_{self.migration_name}.py"
        migration_path = MIGRATIONS_PATH / filename

        with open(migration_path, "w") as f:
            f.write(MIGRATION_TEMPLATE.format(self.migration_name, ts))

        print(f"Migration '{self.migration_name}' generated successfully.")

    def __validate_migration_name(self, name):
        if not name.isidentifier():
            raise ValueError("Migration name must be a valid Python identifier.")
