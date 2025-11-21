import json, os, pathlib

class MigrationStatus:
    '''
    Centralized migration status tracker.
    Tracks which migrations have been applied to which files.
    '''
    STATUS_FILE = pathlib.Path(__file__).parent / "migrate" / "status.json"

    @classmethod
    def get_migrations(cls, file_path):
        '''
        Returns a list of migration versions that have been applied to the given file.
        '''
        status = cls._load_status()
        file_key = str(pathlib.Path(file_path).absolute())
        return status.get(file_key, [])

    @classmethod
    def add_migration(cls, file_path, version):
        '''
        Records that a migration version has been applied to a file.
        '''
        status = cls._load_status()
        file_key = str(pathlib.Path(file_path).absolute())

        if file_key not in status:
            status[file_key] = []

        if version not in status[file_key]:
            status[file_key].append(version)

        cls._save_status(status)

    @classmethod
    def remove_migration(cls, file_path, version):
        '''
        Records that a migration version has been rolled back from a file.
        '''
        status = cls._load_status()
        file_key = str(pathlib.Path(file_path).absolute())

        if file_key in status and version in status[file_key]:
            status[file_key].remove(version)

        cls._save_status(status)

    @classmethod
    def _load_status(cls):
        '''
        Loads the migration status from the status file.
        Returns an empty dict if the file doesn't exist.
        '''
        if not os.path.exists(cls.STATUS_FILE):
            return {}

        try:
            with open(cls.STATUS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    @classmethod
    def _save_status(cls, status):
        '''
        Saves the migration status to the status file.
        '''
        with open(cls.STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
