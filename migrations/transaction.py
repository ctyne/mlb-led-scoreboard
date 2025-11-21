import json, os, pathlib, shutil

from migrations.exceptions import Rollback

class Transaction:
    TEMP_EXTENSION = ".migrate"

    def __init__(self):
        self._backups = []

        self._active = False

    def __enter__(self):
        self.begin()

        return self
    
    def begin(self):
        if self._active:
            return

        print("\tBEGIN TRANSACTION")
        self._active = True
    
    def write(self, path, data):
        if os.path.exists(path):
            if not isinstance(path, pathlib.Path):
                path = pathlib.Path(path)

            print("\t\tSTAGING:", path)

            backup = path.with_suffix(self.TEMP_EXTENSION)

            shutil.copy2(path, backup)
            self._backups.append((path, backup))

        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2)

        with open(path, 'w') as f:
            f.write(data)

    def rollback(self):
        for orig, backup in self._backups:
            shutil.move(backup, orig)

    def commit(self):
        for _, backup in self._backups:
            os.remove(backup)

        print("\tCOMMIT TRANSACTION")

    def __exit__(self, exc_type, exc_value, traceback):
        try: 
            if exc_type is None:
                self.commit()
            else:
                raise exc_type(exc_value).with_traceback(traceback)
        except Rollback:
            print("\tROLLBACK TRANSACTION")
            self.rollback()
        except Exception as e:
            print(f"\tROLLBACK TRANSACTION: {e}")
            self.rollback()
