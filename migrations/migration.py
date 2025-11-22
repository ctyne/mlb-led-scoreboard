from migrations.mode import MigrationMode
from migrations.transaction import Transaction
from migrations.status import MigrationStatus
from migrations.manager import MigrationManager


class ConfigMigration:
    """
    Base class for configuration migrations.

    When up() or down() is executed, the self.txn attribute is automatically set
    and can be used to read/write files atomically within migration methods.
    """

    def __init__(self, version: str):
        self.version = version

    def up(self, txn: Transaction):
        """
        Performs a data migration for a configuration object.
        """
        raise NotImplementedError("ConfigMigration subclasses must implement up()")

    def down(self, txn: Transaction):
        """
        Reverse a migration.

        Raises IrreversibleMigration if migration cannot be reversed.
        Default implementation assumes an irreversible migration.
        """
        raise NotImplementedError("ConfigMigration subclasses must implement down()")

    def execute(self, mode: MigrationMode):
        with Transaction() as txn:
            if mode == MigrationMode.DOWN:
                result = self.down(txn)
            elif mode == MigrationMode.UP:
                result = self.up(txn)

            # Update status files in the same transaction
            modified_files = txn.get_modified_files()
            custom_status, schema_status = MigrationStatus.build_updated_migration_statuses(self.version, mode, modified_files)

            txn.write(
                MigrationManager.normalize_path(MigrationStatus.CUSTOM_STATUS_FILE),
                custom_status
            )
            txn.write(
                MigrationManager.normalize_path(MigrationStatus.SCHEMA_STATUS_FILE),
                schema_status
            )

        return result
