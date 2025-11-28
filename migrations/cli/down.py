from migrations.migration import MigrationMode
from migrations.cli.command import CLICommand
from migrations.plan import MigrationExecutionPlan


class Down(CLICommand):
    """
    Rolls back a migration or multiple migrations, if --step is specified.
    """

    def __init__(self, arguments):
        self.step = arguments.step

    def execute(self):
        print("Rolling back migrations...")

        plan = MigrationExecutionPlan.build(mode=MigrationMode.DOWN)

        if not plan.has_work(mode=MigrationMode.DOWN):
            print("No migrations to roll back.")
            return

        # Process migrations in reverse order for rollback
        for migration in reversed(plan.migrations):
            files_to_rollback = plan.get_files_having(migration.version)

            if not files_to_rollback:
                print(f"ROLLBACK {migration.version} - No files have this migration, skipping.")
                continue

            print("=" * 80)
            print(f"ROLLBACK {migration.version} << {migration.__class__.__name__} >>")

            migration.execute(MigrationMode.DOWN, target_files=files_to_rollback)

            self.step -= 1
            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
