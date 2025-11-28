import json, os, pathlib, shutil

from enum import Enum
from contextlib import contextmanager
from migrations.exceptions import *

# Track active transaction to prevent nesting.
# The transaction system is designed specifically for migrations, so a full-fledged nested transaction system is not needed.
_active_transaction = None


class TransactionState(Enum):
    UNSTARTED = 1
    OPEN = 2
    COMMITTED = 3
    ROLLED_BACK = 4


class Transaction:
    """Generic transaction class for atomic file operations."""

    TXN_DIRECTORY = pathlib.Path(__file__).parent / "migrate" / ".transaction"

    def __init__(self):
        """
        Create a transaction for atomic file operations.
        """
        self._open = {}
        self._state = TransactionState.UNSTARTED
        self._temp_dir = None
        self._file_counter = 0

    @property
    def state(self):
        return self._state

    def __enter__(self):
        self.begin()

        return self

    def begin(self):
        global _active_transaction

        if self.state == TransactionState.OPEN:
            return

        if self.state != TransactionState.UNSTARTED:
            raise TransactionAlreadyCommitted

        # Prevent nested transactions
        if _active_transaction is not None:
            raise ExistingTransaction("Nested transactions are not supported. A transaction is already active.")

        # Create temporary directory for atomic operations
        self._temp_dir = pathlib.Path(Transaction.TXN_DIRECTORY)
        self._temp_dir.mkdir(exist_ok=True)

        print("\tBEGIN TRANSACTION")
        self._state = TransactionState.OPEN
        _active_transaction = self

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
        Removes temporary directory without overwriting to reference paths.
        """
        global _active_transaction

        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)

        self._state = TransactionState.ROLLED_BACK
        _active_transaction = None
        print("\tROLLBACK TRANSACTION")

    def get_modified_files(self) -> list[pathlib.Path]:
        """
        Returns a list of original file paths that have been modified in this transaction.
        """
        return list(self._open.values())

    def commit(self):
        """
        Swaps in the temporary files to their original paths, then removes temp directory.
        """
        global _active_transaction

        if not self._open:
            print("\t\tWARNING: Nothing staged!")
            return self.rollback()

        for dirty, orig in self._open.items():
            shutil.move(dirty, orig)

        # Clean up temp directory
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)

        self._state = TransactionState.COMMITTED
        _active_transaction = None
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
        global _active_transaction

        try:
            if exc_type is None:
                self.commit()
                return False

            try:
                self.rollback()

                # Suppress Rollback exceptions only
                return exc_type == Rollback
            except Exception as rollback_error:
                print(f"\tWARNING: Rollback failed: {rollback_error}")

            return False
        finally:
            # Always clear active transaction when exiting
            _active_transaction = None

    def __create_transaction_file(self, path: pathlib.Path) -> pathlib.Path:
        """
        Creates a new file for the transaction in the temporary directory.
        The transaction must be active. Files are cleaned up after the transaction commits or rolls back.
        """
        if not self.state == TransactionState.OPEN:
            raise TransactionNotOpen("Transactions must be opened before use.")
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")

        # Check if this file is already staged
        for dirty, orig in self._open.items():
            if orig == path:
                return dirty

        # Create unique temp file in temp directory
        dirty = self._temp_dir / f"{self._file_counter}_{path.name}"
        self._file_counter += 1

        shutil.copy(path, dirty)
        self._open[dirty] = path

        print("\t\tSTAGING:", path)

        return dirty
