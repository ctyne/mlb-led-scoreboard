import json, os, pathlib
from migrations.mode import MigrationMode


class MigrationStatus:
    """
    Centralized migration status tracker.
    Tracks which migrations have been applied to which files.
    """

    CUSTOM_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "custom-status.json"
    SCHEMA_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "schema-status.json"

    @staticmethod
    def pending_migrations():
        """
        Returns a list of migration versions that have yet to be applied.
        """
        from migrations.manager import MigrationManager

        pending = set()

        for migration in MigrationManager.load_migrations():
            migrated = False
            for migrations in MigrationStatus.load_status().values():
                if migration.version in migrations:
                    migrated = True
                    break

            if not migrated:
                pending.add(migration)

        return pending

    @classmethod
    def get_migrations(cls, file_path: pathlib.Path) -> list[str]:
        """
        Returns a list of migration versions that have been applied to the given file.
        """
        from migrations.manager import MigrationManager

        status = cls.load_status()
        file_key = MigrationManager.normalize_path(file_path)
        return status.get(file_key, [])

    @classmethod
    def load_status(cls):
        """
        Loads the migration status from the status file.
        Returns an empty dict if the file doesn't exist.
        """
        return cls._load_status(cls.CUSTOM_STATUS_FILE) | cls._load_status(cls.SCHEMA_STATUS_FILE)

    @classmethod
    def _load_status(cls, path: pathlib.Path) -> dict:
        if not os.path.exists(path):
            return {}

        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    @staticmethod
    def build_updated_migration_statuses(
        version: str, mode: MigrationMode, modified_files: list[pathlib.Path]
    ) -> tuple[dict, dict]:
        """
        Creates two dictionaries containing updated status data for custom and schema files.
        """
        from migrations.manager import MigrationManager

        if not modified_files:
            return {}, {}

        custom_status = {}
        schema_status = {}

        # Load existing status
        for path, versions in MigrationStatus.load_status().items():
            if MigrationManager.is_schema(path):
                schema_status[path] = versions
            else:
                custom_status[path] = versions

        # Update status for each modified file
        for file_path in modified_files:
            file_key = MigrationManager.normalize_path(file_path)

            if MigrationManager.is_schema(file_key):
                status = schema_status
            else:
                status = custom_status

            if file_key not in status:
                status[file_key] = []

            if mode == MigrationMode.UP:
                if version not in status[file_key]:
                    status[file_key].append(version)
            elif mode == MigrationMode.DOWN:
                if version in status[file_key]:
                    status[file_key].remove(version)

        return custom_status, schema_status
