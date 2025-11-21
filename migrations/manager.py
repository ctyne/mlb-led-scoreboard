import json, os, pathlib

BASE_PATH = pathlib.Path(__file__).parent.parent
COLORS_PATH = BASE_PATH / "colors"
COORDINATES_PATH = BASE_PATH / "coordinates"


class MigrationManager:
    '''
    Loads migration classes from the migrations directory.
    Each migration file should have a name starting with a timestamp.
    '''
    _configs = None

    @staticmethod
    def load_migrations():
        '''
        Dynamically loads migration classes and instantiates them.
        '''
        migrations = []

        for path in sorted((pathlib.Path(__file__).parent).glob("*.py")):
            if path.name[0].isdigit():
                migration_module = getattr(__import__("migrations." + path.stem), path.stem)
                version, migration_class_name = path.stem.split('_', 1)
                migration_class = getattr(migration_module, migration_class_name)

                migrations.append(migration_class(version))

        return migrations

    @classmethod
    def fetch_configs(cls):
        '''
        Returns a list of configurations that are able to be migrated.
        '''
        if cls._configs is not None:
            return cls._configs

        cls._configs = []

        paths = [BASE_PATH, COLORS_PATH, COORDINATES_PATH]

        for path in paths:
            for entry in os.listdir(path):
                if entry.endswith(".json") and "emulator" not in entry:
                    json_path = pathlib.Path(path) / entry
                    cls._configs.append(
                        (json_path, MigrationManager.get_migrations(json_path))
                    )

        return cls._configs


    @staticmethod
    def get_migrations(path):
        '''
        Reads the list of migrations that have been applied to a file.
        Returns empty list if file doesn't exist or has no migrations.
        '''
        try:
            with open(path, 'r') as f:
                data = json.load(f)

            migrations = data.get("_migrations", [])

            return migrations
        except (FileNotFoundError, json.JSONDecodeError):
            return []
