from migrations.manager import MigrationManager
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

        for migration in migrations[::-1]:
            print("=" * 80)
            print(f"ROLLBACK {migration.version} << {migration.__class__.__name__} >>")

            if MigrationManager.last_checkpoint() == migration.version:
                migration.down()
                MigrationManager.remove_checkpoint()

                self.step -= 1
            else:
                print("\t-- Migration not yet executed, skipping migration. --")

            if self.step == 0:
                break

        print("=" * 80)
        print("Done.")
