import json
import pathlib
import shutil

from migrations.cli.command import CLICommand
from migrations.manager import MigrationManager
from migrations.status import MigrationStatus

class Init(CLICommand):
    def __init__(self, _arguments):
        pass

    def execute(self):
        '''
        Initialize custom config files by copying from schema files (*.example.json).
        New files inherit migration status from schemas.
        Existing files are skipped (they need migration from their current version).
        '''
        print("Initializing config files from schemas...")

        project_root = pathlib.Path(__file__).parent.parent.parent
        search_dirs = [
            project_root,
            project_root / "coordinates",
            project_root / "colors"
        ]

        # Load schema status (what migrations schemas have)
        schema_status = MigrationStatus._load_status(MigrationStatus.SCHEMA_STATUS_FILE)

        # Load existing custom status
        custom_status = MigrationStatus._load_status(MigrationStatus.CUSTOM_STATUS_FILE)

        copied_files = []
        skipped_files = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for schema_file in search_dir.glob("*.example.json"):
                # Derive target filename (strip .example)
                target_file = schema_file.with_suffix("").with_suffix(".json")

                if target_file.exists():
                    # File exists = user has old config that needs migration
                    skipped_files.append(str(target_file.relative_to(project_root)))
                    continue

                # Copy schema file to target
                shutil.copy2(schema_file, target_file)

                # Inherit migration status from schema
                schema_key = MigrationManager.normalize_path(schema_file)
                target_key = MigrationManager.normalize_path(target_file)
                if schema_key in schema_status:
                    custom_status[target_key] = schema_status[schema_key].copy()

                copied_files.append(str(target_file.relative_to(project_root)))

        # Save custom status atomically (write-then-swap) if we copied any files
        if copied_files:
            with open(MigrationStatus.CUSTOM_TXN_FILE, 'w') as f:
                json.dump(custom_status, f, indent=2)
            shutil.move(MigrationStatus.CUSTOM_TXN_FILE, MigrationStatus.CUSTOM_STATUS_FILE)

        # Report results
        print("=" * 80)
        if copied_files:
            print(f"Created {len(copied_files)} config file(s) from schemas:")
            for f in copied_files:
                print(f"  - {f}")
            print(f"\nThese files inherit all migrations from their schemas.")

        if skipped_files:
            if copied_files:
                print()
            print(f"Skipped {len(skipped_files)} existing file(s):")
            for f in skipped_files:
                print(f"  - {f}")
            print(f"\nExisting files need to be migrated with 'migrate up'.")

        if not copied_files and not skipped_files:
            print("No schema files (*.example.json) found.")

        print("=" * 80)
