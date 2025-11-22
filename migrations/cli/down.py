from migrations.manager import MigrationManager
from migrations.migration import MigrationMode
from migrations.cli.command import CLICommand


class Down(CLICommand):
    def __init__(self, arguments):
        self.step = arguments.step

    def execute(self):
        print("Rolling back migrations...")

        migrations = MigrationManager.load_migrations()
        if len(migrations) == 0:
            print("No migrations to roll back.")
            return

        configs = MigrationManager.fetch_configs()

        for migration in migrations[::-1]:
            print("=" * 80)
            print(f"ROLLBACK {migration.version} << {migration.__class__.__name__} >>")

            targets = []

            for config_file, applied_migrations in configs:
                if migration.version in applied_migrations:
                    targets.append(config_file)

            if targets:
                migration.execute(MigrationMode.DOWN)
                self.step -= 1
            else:
                print("\t-- Migration not yet applied to any files, skipping. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
