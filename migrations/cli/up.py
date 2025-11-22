from migrations.manager import MigrationManager
from migrations.migration import MigrationMode
from migrations.cli.command import CLICommand


class Up(CLICommand):
    def __init__(self, arguments):
        self.step = arguments.step

    def execute(self):
        print("Executing migrations...")

        migrations = MigrationManager.load_migrations()
        if len(migrations) == 0:
            print("No migrations to execute.")
            return

        configs = MigrationManager.fetch_configs()

        for migration in migrations:
            print("=" * 80)
            print(f"MIGRATE {migration.version} << {migration.__class__.__name__} >>")

            targets = []

            for config_file, applied_migrations in configs:
                if migration.version in applied_migrations:
                    targets.append(config_file)

            # If we have targets, this migration is already applied.
            if not targets:
                migration.execute(MigrationMode.UP)
                self.step -= 1
            else:
                print("\t-- All files up to date, skipping migration. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
