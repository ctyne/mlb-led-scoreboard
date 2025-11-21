from migrations.manager import MigrationManager
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

        for migration in migrations:
            print("=" * 80)
            print(f"MIGRATE {migration.version} << {migration.__class__.__name__} >>")

            if MigrationManager.last_checkpoint() < migration.version:
                migration.up()
                MigrationManager.create_checkpoint(migration.version)

                self.step -= 1
            else:
                print("\t-- Up to date, skipping migration. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
