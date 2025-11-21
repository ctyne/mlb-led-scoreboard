from migrations.manager import MigrationManager, CHECKPOINT_PATH
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

        for version, migration_class in migrations[::-1]:
            print("=" * 80)
            print(f"ROLLBACK {version} << {migration_class.__name__} >>")

            migration = migration_class()

            if self.last_checkpoint() == version:
                migration.down()
                self.create_checkpoint()

                self.step -= 1
            else:
                print("\t-- Migration not yet executed, skipping migration. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
        

    def create_checkpoint(self):
        with open(CHECKPOINT_PATH, 'r+') as f:
            checkpoints = f.readlines()
            f.seek(0)
            f.writelines(checkpoints[:-1])
            f.truncate()

    def last_checkpoint(self):
        try:
            with open(CHECKPOINT_PATH, 'r') as f:
                checkpoints = f.readlines()
                return checkpoints[-1].strip()
        except (FileNotFoundError, IndexError):
            return "0"
