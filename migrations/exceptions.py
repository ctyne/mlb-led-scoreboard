class IrreversibleMigration(Exception):
    pass


class Rollback(Exception):
    pass


class ExistingTransaction(Exception):
    pass


class TransactionNotOpen(Exception):
    pass


class TransactionAlreadyCommitted(Exception):
    pass
