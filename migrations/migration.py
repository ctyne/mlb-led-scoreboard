from typing import Optional
import pathlib

from migrations.mode import MigrationMode
from migrations.status import MigrationStatus
from migrations.context import MigrationContext


class ConfigMigration:
    """
    Base class for configuration migrations.
    """

    def __init__(self, version: str):
        self.version = version

    def up(self, ctx: MigrationContext):
        """Performs a data migration using the context's methods."""
        raise NotImplementedError("ConfigMigration subclasses must implement up()")

    def down(self, ctx: MigrationContext):
        """
        Reverses a migration using the context's methods.

        Raises IrreversibleMigration if migration cannot be reversed.
        """
        raise NotImplementedError("ConfigMigration subclasses must implement down()")

    def execute(self, mode: MigrationMode, target_files: Optional[list[pathlib.Path]] = None):
        """
        Executes the migration in the given mode.
        If target_files is provided, only those files will be operated on.
        """
        with MigrationContext(target_files=target_files) as ctx:
            if mode == MigrationMode.DOWN:
                result = self.down(ctx)
            elif mode == MigrationMode.UP:
                result = self.up(ctx)

            custom_status, schema_status = MigrationStatus.build_updated_migration_statuses(self.version, mode)

            if custom_status.dirty:
                ctx.write(MigrationStatus.CUSTOM_STATUS_FILE, custom_status.data)
            if schema_status.dirty:
                ctx.write(MigrationStatus.SCHEMA_STATUS_FILE, schema_status.data)

        return result

    @property
    def filename(self):
        """
        Returns the migration filename.
        Child classes will always have the same file structure, so hardcoding here is simplest.
        """
        return f"{self.version}_{self.__class__.__name__}.py"
