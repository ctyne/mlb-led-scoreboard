import json, os, pathlib, shutil

from enum import Enum
from contextlib import contextmanager
from migrations.exceptions import Rollback, TransactionNotOpen, TransactionAlreadyCommitted


class TransactionState(Enum):
    UNSTARTED = 1
    OPEN = 2
    COMMITTED = 3


class Transaction:
    """Generic transaction class for atomic file operations."""

    TXN_EXTENSION = ".txn"

    def __init__(self):
        """
        Create a transaction for atomic file operations.
        """
        self._open = {}
        self._state = TransactionState.UNSTARTED

    @property
    def state(self):
        return self._state

    def __enter__(self):
        self.begin()

        return self

    def begin(self):
        if self.state == TransactionState.OPEN:
            return

        if self.state != TransactionState.UNSTARTED:
            raise TransactionAlreadyCommitted

        print("\tBEGIN TRANSACTION")
        self._state = TransactionState.OPEN

    def read(self, path: pathlib.Path) -> dict:
        """
        Reads from a file in an open transaction.

        This must be used over raw open() calls as the transaction masks writing to a transaction file and atomically swaps in the migrated file after the transaction commits.
        If not used, data written within the transaction will not be visible.
        """
        dirty = self.__create_transaction_file(path)

        with open(dirty, "r") as f:
            data = json.load(f)

        return data

    def write(self, path: pathlib.Path, data: dict):
        """
        Writes to a file in an open transaction.
        """
        dirty = self.__create_transaction_file(path)

        with open(dirty, "w") as f:
            json.dump(data, f, indent=2)

    def rollback(self):
        """
        Removes temporary files without overwriting to reference paths.
        """
        for dirty, _ in self._open.items():
            if os.path.exists(dirty):
                os.remove(dirty)

    def get_modified_files(self) -> list[pathlib.Path]:
        """
        Returns a list of original file paths that have been modified in this transaction.
        """
        return list(self._open.values())

    def commit(self):
        """
        Swaps in the temporary dirty files to their original reference path, overwriting existing files.
        """
        if not self._open:
            print("\t\tWARNING: Nothing staged!")
            return

        for dirty, orig in self._open.items():
            shutil.move(dirty, orig)

        self._state = TransactionState.COMMITTED
        print("\tCOMMIT TRANSACTION")

    @contextmanager
    def load_for_update(self, file_path):
        """
        Loads content from the file within a transaction within a context.
        Content is a dictionary representing JSON data.
        Content is written back to the file after exiting the context.

        Guarantees data written will be updated atomically.
        """

        content = self.read(file_path)

        yield content

        self.write(file_path, content)

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

    def __create_transaction_file(self, path: pathlib.Path) -> pathlib.Path:
        """
        Creates a new file for the transaction. The transaction must be active.
        The file has an extension `TXN_EXTENSION` and is cleaned up after the transaction commits or rolls back.
        """
        if not self.state == TransactionState.OPEN:
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

        print("\t\tSTAGING:", path)

        return dirty
