import json, os, pathlib

class MigrationStatus:
    '''
    Centralized migration status tracker.
    Tracks which migrations have been applied to which files.
    '''
    TXN_EXTENSION = ".txn"
    CUSTOM_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "custom-status.json"
    CUSTOM_TXN_FILE = CUSTOM_STATUS_FILE.with_suffix(TXN_EXTENSION)

    SCHEMA_STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "schema-status.json"
    SCHEMA_TXN_FILE = SCHEMA_STATUS_FILE.with_suffix(TXN_EXTENSION)

    @classmethod
    def get_migrations(cls, file_path):
        '''
        Returns a list of migration versions that have been applied to the given file.
        '''
        from migrations.manager import MigrationManager
        status = cls.load_status()
        file_key = MigrationManager.normalize_path(file_path)
        return status.get(file_key, [])

    @classmethod
    def load_status(cls):
        '''
        Loads the migration status from the status file.
        Returns an empty dict if the file doesn't exist.
        '''
        return cls._load_status(cls.CUSTOM_STATUS_FILE) | cls._load_status(cls.SCHEMA_STATUS_FILE)

    @classmethod
    def _load_status(cls, path):
        if not os.path.exists(path):
            return {}

        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}