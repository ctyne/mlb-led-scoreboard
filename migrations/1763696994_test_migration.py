from migrations.migration import ConfigMigration


class test_migration(ConfigMigration):
    def up(self):
        raise NotImplementedError("Migration logic not implemented.")

    # def down(self):
    #     Implement the logic to revert the migration if necessary.
    #     Raises IrreversibleMigration by default.
