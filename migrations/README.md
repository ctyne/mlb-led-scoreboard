# Configuration Migration System

A version control system for configuration files that allows safe, automated schema upgrades.

## Quick Start

### First Time Setup

```bash
# Copy schema files to create your configs (inherits current migration state)
python -m migrations init
```

### Creating a Migration

Migrations are generated with the `generate` command and must be a valid Python identifier.

```bash
# Generate a new migration file
python -m migrations generate example_migration

# Edit the generated file
# migrations/migrate/{timestamp}_example_migration.py
```

### Running Migrations

```bash
# Apply all pending migrations
python -m migrations up

# Rollback the last migration
python -m migrations down

# Rollback the last 5 migrations
python -m migrations down --step 5
```

## Writing Migrations

Every migration needs to define at minimum `up()` to apply changes. `down()` is optional and reverts an `up()` migration. If `down()` is not defined, the migration is irreversible and raise an exception if rollback is attempted.

### Basic Examples

The following is an example of adding a key to all configurations.

```python
from migrations.migration import ConfigMigration
from migrations.manager import MigrationManager

class example_migration(ConfigMigration):
    def up(self):
        '''Add example key to all configs'''
        self.add_key("example", 1, MigrationManager.all_configs())

    def down(self):
        '''Remove example key'''
        self.remove_key("example", MigrationManager.all_configs())
```

Below are some more advanced uses:

```python
# Add a key to a specific config.
def up(self):
    self.add_key("example", 1, "config.json")

# Add a deeply nested key. Strings delimited with dots are treated as a nested path.
def up(self):
    self.add_key("path.to.key", "example", "config.json")

# Read existing content, and modify it in-place.
def up(self):
    for content in self.enumerate_configs("config.json"):
        old_value = content["path"]["to"]["key"]

        content["path"]["to"]["key"] = old_value.replace("_", "-")
```

## Atomicity Guarantees

If using the helpers shown above, the migration system makes strong guarantees about atomicity -- ALL operations in a migration are guaranteed to complete else ALL operations fail.

Under the hood, the migration system uses a transaction manager that compiles all changes made by a migration. The changes are written to a temporary file with a `.txn` extension. Once all changes are complete, the transaction manager copies the transaction file to the reference path, overwriting the old configuration.

---------------
> [!WARNING]  
> **Deviate from these patterns at your own risk!**
>
> Failure to follow the correct patterns can leave the migrator in invalid states.
---------------


## Tracking Migration State

The system maintains two snapshot files that record which migrations have been applied to which files:

* `migrations/migrate/schema-status.json`
  - Tracks migrations applied to schema files (`*.schema.json`). This file is committed to keep schemas in sync.
* `migrations/migrate/custom-status.json`
  - Tracks migrations applied to your custom config files. This file is ignored by git since they are custom files.

### Structure

Status files are intended to be human-readable. Each key is a path to a config file, and the values are arrays with each element being the version (timestamp) of a migration.

```json
{
  "config.schema.json": [1763750914, 1763750983],
  "coordinates/w32h32.schema.json": [1763750914]
}
```

File paths are relative to project root with forward slashes for cross-platform compatibility. They are updated with the same atomicity guarantees (modify-then-swap) as any other JSON file.

### Initializing

Running `init` performs two operations:

1. If a schema file exists but no corresponding custom file is present, the migrator copies the schema to the expected custom file path.
   * For instance, `config.schema.json` is copied to `config.json`
2. For each copied file, a record is added to the custom state, inheriting the same migration versions as the schema.

This setup allows for pre-existing custom configurations to be migrated to new versions, while allowing new installations to create up-to-date custom configurations without needing to be migrated separately.

## Commands Reference

```bash
# Initialize configs from schemas
# This operation is idempotent
# (alias: i)
python -m migrations init

# Create new migration
# (alias: g)
python -m migrations generate <name>

# Apply migrations
# (alias: u)
python -m migrations up              # Apply all pending
python -m migrations up --step 2     # Apply next 2 only

# Rollback migrations
# (alias: d)
python -m migrations down            # Rollback last 1
python -m migrations down --step 3   # Rollback last 3
```

## Example Workflow

```bash
# 1. First time setup
python -m migrations init

# 2. Create a new migration
python -m migrations g example_migration

# 3. Edit migrations/migrate/{timestamp}_example_migration.py
# ... implement up() / down() ...

# 4. Test it
python -m migrations up      # Apply
python -m migrations down    # Rollback
python -m migrations up      # Re-apply

# 5. Commit schema & status changes
git add migrations/migrate/schema-status.json *.schema.json
git commit -m "Add example_migration field"
```
