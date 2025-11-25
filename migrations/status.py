import json, os, pathlib
from migrations.mode import MigrationMode

class MigrationStatusData:
    """
    An object containing the migrations applied against files as a writable JSON dict in its `data` field.
    The state is always consistent, but may be dirty, which will be contained in the 'dirty' field.
    """

    def __init__(self):
        self.data = {}
        self.dirty = False

    def set_versions(self, file: pathlib.Path, versions: list[str]) -> None:
        """
        Sets the key in the data field to the list of versions.
        """
        self.data[file] = versions

    def add_version(self, file: pathlib.Path, version: str) -> None:
        """
        Adds a version to a file. If the file isn't already tracked, adds the file to tracking before adding the version.

        Always sets the dirty flag.
        """
        if file not in self.data:
            self.data[file] = [version]
            self.dirty = True
        elif version not in self.data[file]:
            self.data[file].append(version)
            self.dirty = True

    def remove_version(self, file: pathlib.Path, version: str) -> None:
        """
        Removes a version from a file. If the file isn't tracked or the version isn't applied to the file, it does nothing.

        If a version is actually removed, sets the dirty flag.
        """
        if file not in self.data:
            return
        
        if version not in self.data[file]:
            return

        self.data[file].remove(version)
        self.dirty = True

        if not self.data[file]:
            del self.data[file]

class MigrationStatus:
    """
    Centralized migration status tracker.
    Tracks which migrations have been applied to which files.
    """

    CUSTOM_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "custom-status.json"
    SCHEMA_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "schema-status.json"

    @staticmethod
    def pending_migrations() -> list:
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

    @staticmethod
    def load_status():
        """
        Loads the migration status from the status file.
        Returns an empty dict if the file doesn't exist.
        """
        return MigrationStatus._load_status(MigrationStatus.CUSTOM_STATUS_FILE) | MigrationStatus._load_status(
            MigrationStatus.SCHEMA_STATUS_FILE
        )

    @staticmethod
    def _load_status(path: pathlib.Path) -> dict:
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
    ) -> tuple[MigrationStatusData, MigrationStatusData]:
        """
        Creates two MigrationStatusData objects containing updated status data for custom and schema files.
        """
        from migrations.manager import MigrationManager

        custom_status = MigrationStatusData()
        schema_status = MigrationStatusData()

        if not modified_files:
            return custom_status, schema_status

        # Load existing status
        for path, versions in MigrationStatus.load_status().items():
            if MigrationManager.is_schema(path):
                schema_status.set_versions(path, versions)
            else:
                custom_status.set_versions(path, versions)

        # Update status for each modified file
        for file_path in modified_files:
            file_key = MigrationManager.normalize_path(file_path)

            if MigrationManager.is_schema(file_key):
                status = schema_status
            else:
                status = custom_status

            if mode == MigrationMode.UP:
                status.add_version(file_key, version)
            elif mode == MigrationMode.DOWN:
                status.remove_version(file_key, version)

        return custom_status, schema_status
