from migrations.manager import MigrationManager, CHECKPOINT_PATH
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

        for version, migration_class in migrations:
            print("=" * 80)
            print(f"MIGRATE {version} << {migration_class.__name__} >>")

            migration = migration_class()

            if self.last_checkpoint() < version:
                migration.up()
                self.create_checkpoint(version)

                self.step -= 1
            else:
                print("\t-- Up to date, skipping migration. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")

    def create_checkpoint(self, ts):
        with open(CHECKPOINT_PATH, 'a') as f:
            f.write(f"{ts}\n")

    def last_checkpoint(self):
        try:
            with open(CHECKPOINT_PATH, 'r') as f:
                checkpoints = f.readlines()
                return checkpoints[-1].strip()
        except (FileNotFoundError, IndexError):
            return "0"
