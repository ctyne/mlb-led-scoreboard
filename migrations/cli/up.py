from migrations.migration import MigrationMode
from migrations.cli.command import CLICommand
from migrations.plan import MigrationExecutionPlan


class Up(CLICommand):
    """
    Migrates all pending migrations, unless --step is specified. If step is present, migrates up to that amount.
    """

    def __init__(self, arguments):
        self.step = arguments.step

    def execute(self):
        print("Executing migrations...")

        plan = MigrationExecutionPlan.build(mode=MigrationMode.UP)

        if not plan.has_work(mode=MigrationMode.UP):
            print("No migrations to execute.")
            return

        for migration in plan.migrations:
            files_to_migrate = plan.get_files_needing(migration.version)

            if not files_to_migrate:
                print(f"MIGRATE {migration.version} - All files up to date, skipping.")
                continue

            print("=" * 80)
            print(f"MIGRATE {migration.version} << {migration.__class__.__name__} >>")

            migration.execute(MigrationMode.UP, target_files=files_to_migrate)

            self.step -= 1
            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
