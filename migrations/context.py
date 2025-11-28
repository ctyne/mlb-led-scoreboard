class MigrationContext:
    """
    Context for migration execution.

    Provides metadata like target files that can be passed to migrations and helpers
    to control which files are operated on.

    Usage:
        with MigrationContext(target_files=[...]) as context:
            migration.up(txn, context)
    """
    def __init__(self, target_files=None):
        self.target_files = set(target_files) if target_files else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass
