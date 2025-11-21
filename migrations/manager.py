import os, pathlib, shutil

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

                migrations.append(migration_class(version))

        return migrations
    
    @staticmethod
    def remove_checkpoint():
        """Remove the last checkpoint atomically using temp file swap."""
        temp_path = CHECKPOINT_PATH.with_suffix('.txn')
        try:
            with open(CHECKPOINT_PATH, 'r') as existing:
                checkpoints = existing.readlines()

            with open(temp_path, 'w') as f:
                f.writelines(checkpoints[:-1])

            shutil.move(temp_path, CHECKPOINT_PATH)
        except FileNotFoundError:
            pass

    @staticmethod
    def create_checkpoint(checkpoint):
        """Add a new checkpoint atomically using temp file swap."""
        temp_path = CHECKPOINT_PATH.with_suffix('.txn')
        with open(temp_path, 'w') as f:
            try:
                with open(CHECKPOINT_PATH, 'r') as existing:
                    f.write(existing.read())
            except FileNotFoundError:
                pass

            f.write(f"{checkpoint}\n")

        shutil.move(temp_path, CHECKPOINT_PATH)

    @staticmethod
    def last_checkpoint():
        try:
            with open(CHECKPOINT_PATH, 'r') as f:
                checkpoints = f.readlines()
                return checkpoints[-1].strip()
        except (FileNotFoundError, IndexError):
            return "0"

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
