import json, os, pathlib, shutil

from migrations.exceptions import Rollback, TransactionNotOpen

class Transaction:
    TXN_EXTENSION = ".txn"

    def __init__(self):
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

        data = None
        with open(dirty, "r") as f:
            data = json.load(f)

        return data
    
    def write(self, path, data):
        '''
        Writes to a file in an open transaction.
        '''
        print("\t\tSTAGING:", path)

        dirty = self.__create_transaction_file(path)

        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2)

        with open(dirty, 'w') as f:
            f.write(data)

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
        '''
        for dirty, orig in self._open.items():
            shutil.move(dirty, orig)

        print("\tCOMMIT TRANSACTION")

    def __exit__(self, exc_type, exc_value, traceback):
        try: 
            if exc_type is None:
                self.commit()
            else:
                raise exc_type(exc_value).with_traceback(traceback)
        except Rollback:
            print("\tROLLBACK TRANSACTION")
        except Exception as e:
            print(f"\tROLLBACK TRANSACTION: {e}")
        finally:
            self.rollback()

    def __create_transaction_file(self, path):
        '''
        Creates a new file for the transaction. The transaction must be active.
        The file has an extension TXN_EXTENSION and is cleaned up after the transaction commits or rolls back.
        '''
        if not self._active:
            raise TransactionNotOpen("Transactions must be opened before use.")
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")
        
        dirty = path.with_suffix(self.TXN_EXTENSION)

        if path in self._open:
            return

        shutil.copy(path, dirty)
        self._open[dirty] = path

        return dirty
