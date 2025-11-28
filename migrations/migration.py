from typing import Optional
import pathlib

from migrations.mode import MigrationMode
from migrations.transaction import Transaction
from migrations.status import MigrationStatus
from migrations.context import MigrationContext


class ConfigMigration:
    """
    Base class for configuration migrations.
    """

    def __init__(self, version: str):
        self.version = version

    def up(self, txn: Transaction, ctx: MigrationContext):
        """Performs a data migration. Pass ctx to helpers to limit which files are migrated."""
        raise NotImplementedError("ConfigMigration subclasses must implement up()")

    def down(self, txn: Transaction, ctx: MigrationContext):
        """
        Reverses a migration. Pass ctx to helpers to limit which files are rolled back.

        Raises IrreversibleMigration if migration cannot be reversed.
        """
        raise NotImplementedError("ConfigMigration subclasses must implement down()")

    def execute(self, mode: MigrationMode, target_files: Optional[list[pathlib.Path]] = None):
        """
        Executes the migration in the given mode.
        If target_files is provided, only those files will be operated on.
        """
        with MigrationContext(target_files=target_files) as ctx:
            with Transaction() as txn:
                if mode == MigrationMode.DOWN:
                    result = self.down(txn, ctx)
                elif mode == MigrationMode.UP:
                    result = self.up(txn, ctx)

                # Update status files in the same transaction
                modified_files = txn.get_modified_files()
                custom_status, schema_status = MigrationStatus.build_updated_migration_statuses(
                    self.version, mode, modified_files
                )

                if custom_status.dirty:
                    txn.write(MigrationStatus.CUSTOM_STATUS_FILE, custom_status.data)
                if schema_status.dirty:
                    txn.write(MigrationStatus.SCHEMA_STATUS_FILE, schema_status.data)

            return result

    @property
    def filename(self):
        """
        Returns the migration filename.
        Child classes will always have the same file structure, so hardcoding here is simplest.
        """
        return f"{self.version}_{self.__class__.__name__}.py"
