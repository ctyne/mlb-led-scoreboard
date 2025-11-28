class IrreversibleMigration(Exception):
    """Raised if a migration is attempted to be rolled back but cannot be (for instance if the operation is not idempotent)."""

    pass


class Rollback(Exception):
    """Raised when a migration is rolled back, either automatically due to an exception or manually."""

    pass


class ExistingTransaction(Exception):
    """Raised when multiple transactions exist. Transaction nesting is not supported."""

    pass


class TransactionNotOpen(Exception):
    """Raised when a transaction is written to, but is not already open."""

    pass


class TransactionAlreadyCommitted(Exception):
    """Raised when a transaction is attempted to be written to, but is already closed."""

    pass


class UntrackedConfigError(Exception):
    """Raised when config files exist but aren't tracked in the migration system."""

    def __init__(self, untracked_files: list):
        self.untracked_files = untracked_files

        files_list = "\n  - ".join(str(f) for f in untracked_files)
        message = f"""
Found {len(untracked_files)} config file(s) not tracked by the migration system:
  - {files_list}

These files may have been created by manually copying configs (e.g., using 'cp').
To fix this:
  1. Delete the untracked file(s)
  2. Use 'python -m migrations subconfig <name>' to create subconfigs properly
  OR
  1. Run 'python -m migrations reset' to remove all custom configs
  2. Run 'python -m migrations init' to start fresh
"""
        super().__init__(message)
