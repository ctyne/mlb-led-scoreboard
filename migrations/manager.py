import os, pathlib

import pathlib


BASE_PATH = pathlib.Path(__file__).parent.parent
COLORS_PATH = BASE_PATH / "colors"
COORDINATES_PATH = BASE_PATH / "coordinates"

CHECKPOINT_PATH = pathlib.Path(__file__).parent / "checkpoint.txt"


class MigrationManager:
    '''
    Loads migration classes from the migrations directory.
    Each migration file should have a name starting with a timestamp.
    '''
    _configs = None

    @staticmethod
    def load_migrations():
        migrations = []

        for path in sorted((pathlib.Path(__file__).parent).glob("*.py")):
            if path.name[0].isdigit():
                migration_module = getattr(__import__("migrations." + path.stem), path.stem)
                version, migration_class_name = path.stem.split('_', 1)
                migration_class = getattr(migration_module, migration_class_name)

                migrations.append((version, migration_class))

        return migrations

    @classmethod
    def fetch_configs(cls):
        if cls._configs is not None:
            return cls._configs

        cls._configs = {
            "colors": [],
            "coordinates": [],
            "base": []
        }

        paths = [
            (BASE_PATH, "base"),
            (COLORS_PATH, "colors"),
            (COORDINATES_PATH, "coordinates")
        ]

        for path, key in paths:
            for entry in os.listdir(path):
                if entry.endswith(".json") and "emulator" not in entry:
                    cls._configs[key].append(pathlib.Path(path) / entry)

        return cls._configs
