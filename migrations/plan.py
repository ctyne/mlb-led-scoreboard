"""
Migration execution planning.

Provides a structured approach to determining which files need which migrations,
enabling per-file migration tracking instead of all-or-nothing execution.
"""

import pathlib
from typing import Optional

from migrations.mode import MigrationMode
from migrations.manager import MigrationManager


class FileState:
    """Tracks the migration state of a single configuration file."""

    def __init__(self, path: pathlib.Path, applied_migrations: list[str]):
        self.path = path
        self.applied_migrations = set(applied_migrations)
        self.pending_migrations: list = []
        self.rollback_migrations: list = []
        self.is_schema = MigrationManager.is_schema(path)

    def needs_migration(self, version: str) -> bool:
        """For UP: check if migration needs to be applied"""
        return version not in self.applied_migrations

    def has_migration(self, version: str) -> bool:
        """For DOWN: check if migration can be rolled back"""
        return version in self.applied_migrations


class MigrationExecutionPlan:
    """
    Builds and manages a complete execution plan for migrations.

    Loads all configuration files and migrations, then computes which files need which migrations.
    This enables per-file migration tracking instead of all-or-nothing execution.

    Usage:
        # For UP migrations
        plan = MigrationExecutionPlan.build(mode=MigrationMode.UP)
        for migration in plan.migrations:
            files_to_migrate = plan.get_files_needing(migration.version)
            if files_to_migrate:
                migration.execute(MigrationMode.UP, target_files=files_to_migrate)

        # For DOWN migrations
        plan = MigrationExecutionPlan.build(mode=MigrationMode.DOWN)
        for migration in reversed(plan.migrations):
            files_to_rollback = plan.get_files_having(migration.version)
            if files_to_rollback:
                migration.execute(MigrationMode.DOWN, target_files=files_to_rollback)
    """

    def __init__(self):
        self.file_states: dict[pathlib.Path, FileState] = {}
        self.migrations: list = []

    @classmethod
    def build(cls, mode: MigrationMode = MigrationMode.UP) -> "MigrationExecutionPlan":
        """Load all configs and migrations, compute what needs to be done."""
        plan = cls()
        plan.migrations = MigrationManager.load_migrations()

        # Load all files and their current migration state
        configs = MigrationManager.fetch_configs()
        for path, applied_migrations in configs:
            plan.file_states[path] = FileState(path, applied_migrations)

        # Compute pending/rollback migrations for each file
        # Note: Order doesn't matter for these lists - they're only used for has_work() checks
        for file_state in plan.file_states.values():
            for migration in plan.migrations:
                if mode == MigrationMode.UP:
                    if file_state.needs_migration(migration.version):
                        file_state.pending_migrations.append(migration)
                else:  # DOWN
                    if file_state.has_migration(migration.version):
                        file_state.rollback_migrations.append(migration)

        return plan

    def get_files_needing(self, migration_version: str) -> list[pathlib.Path]:
        """For UP: Return list of file paths that need this migration."""
        return [path for path, state in self.file_states.items() if state.needs_migration(migration_version)]

    def get_files_having(self, migration_version: str) -> list[pathlib.Path]:
        """For DOWN: Return list of file paths that have this migration applied."""
        return [path for path, state in self.file_states.items() if state.has_migration(migration_version)]

    def has_work(self, mode: MigrationMode = MigrationMode.UP) -> bool:
        """Check if any files have pending migrations or rollbacks."""
        if mode == MigrationMode.UP:
            return any(state.pending_migrations for state in self.file_states.values())
        else:
            return any(state.rollback_migrations for state in self.file_states.values())

    def mark_applied(self, migration_version: str, file_paths: list[pathlib.Path]) -> None:
        """Mark a migration as applied to the given files. Updates internal state only."""
        for path in file_paths:
            if path in self.file_states:
                self.file_states[path].applied_migrations.add(migration_version)

    def mark_removed(self, migration_version: str, file_paths: list[pathlib.Path]) -> None:
        """Mark a migration as removed from the given files. Updates internal state only."""
        for path in file_paths:
            if path in self.file_states:
                self.file_states[path].applied_migrations.discard(migration_version)
