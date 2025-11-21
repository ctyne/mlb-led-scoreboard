import json, os, pathlib, shutil

from migrations.exceptions import Rollback, TransactionNotOpen
from migrations.manager import MigrationManager
from migrations.mode import MigrationMode
from migrations.status import MigrationStatus

class Transaction:
    TXN_EXTENSION = ".txn"

    def __init__(self, version, mode=MigrationMode.UP):
        '''
        Create a transaction for a migration.
        '''
        self.version = version
        self.mode = mode
        self._open = {}

        self._active = False

    def __enter__(self):
        self.begin()

        return self

    def begin(self):
        if self._active:
            return

        print("\tBEGIN TRANSACTION")
        self._active = True

    def read(self, path):
        '''
        Reads from a file in an open transaction.

        This must be used over raw open() calls as the transaction masks writing to a transaction file and atomically swaps in the migrated file after the transaction commits.
        If not used, data written within the transaction will not be visible.
        '''
        dirty = self.__create_transaction_file(path)

        with open(dirty, "r") as f:
            data = json.load(f)

        return data
    
    def write(self, path, data):
        '''
        Writes to a file in an open transaction.
        '''
        if self.mode == MigrationMode.UP:
            print("\t\tSTAGING:", path)
        else:
            print("\t\tSTAGING ROLLBACK:", path)

        dirty = self.__create_transaction_file(path)

        with open(dirty, 'w') as f:
            json.dump(data, f, indent=2)

    def rollback(self):
        '''
        Removes temporary files without overwriting to reference paths.
        '''
        for dirty, _ in self._open.items():
            if os.path.exists(dirty):
                os.remove(dirty)

    def commit(self):
        '''
        Swaps in the temporary dirty files to their original reference path, overwriting existing files.
        Updates the centralized migration status for all migrated files.
        '''
        if not self._open:
            print("\t\tWARNING: Nothing staged!")
            return

        custom_status = {}
        schema_status = {}

        for path, versions in MigrationStatus.load_status().items():
            if MigrationManager.is_schema(path):
                schema_status[path] = versions
            else:
                custom_status[path] = versions

        for dirty, orig in self._open.items():
            file_key = MigrationManager.normalize_path(orig)

            if MigrationManager.is_schema(file_key):
                status = schema_status
            else:
                status = custom_status

            if file_key not in status:
                status[file_key] = []

            if self.mode == MigrationMode.UP:
                if self.version not in status[file_key]:
                    status[file_key].append(self.version)
            elif self.mode == MigrationMode.DOWN:
                if self.version in status[file_key]:
                    status[file_key].remove(self.version)

        with open(MigrationStatus.CUSTOM_TXN_FILE, 'w') as f:
            json.dump(custom_status, f, indent=2)

        with open(MigrationStatus.SCHEMA_TXN_FILE, 'w') as f:
            json.dump(schema_status, f, indent=2)

        self._open[MigrationStatus.CUSTOM_TXN_FILE] = MigrationStatus.CUSTOM_STATUS_FILE
        self._open[MigrationStatus.SCHEMA_TXN_FILE] = MigrationStatus.SCHEMA_STATUS_FILE

        for dirty, orig in self._open.items():
            shutil.move(dirty, orig)

        print("\tCOMMIT TRANSACTION")

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
            return False

        print("\tROLLBACK TRANSACTION")
        try:
            self.rollback()

            # Suppress Rollback exceptions only
            return exc_type == Rollback
        except Exception as rollback_error:
            print(f"\tWARNING: Rollback failed: {rollback_error}")

        return False

    def __create_transaction_file(self, path):
        '''
        Creates a new file for the transaction. The transaction must be active.
        The file has an extension `TXN_EXTENSION` and is cleaned up after the transaction commits or rolls back.
        '''
        if not self._active:
            raise TransactionNotOpen("Transactions must be opened before use.")
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")
        
        dirty = path.with_suffix(self.TXN_EXTENSION)

        if dirty in self._open:
            return dirty

        shutil.copy(path, dirty)
        self._open[dirty] = path

        return dirty
