# Configuration Migration System

A version control system for configuration files that allows safe, automated changes to JSON configuration files, including files acting as a schema and custom configuration files.

This document is intended for technical users who contribute code to the project. The functionality described here is transparent to most end users. If you have an problem with the migration system, such as during installation or on startup, please open an issue.

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

Every migration needs to define at minimum `up(ctx)` to apply changes. `down(ctx)` is optional and reverts an `up()` migration. If `down()` is not defined, the migration is irreversible and raise an exception if rollback is attempted.

Both methods receive a `MigrationContext` object (`ctx`) which provides helper methods and ensures atomicity across all operations.

### Basic Examples

```python
from migrations import *

class example_migration(ConfigMigration):
    def up(self, ctx: MigrationContext):
        '''Add example key to all configs'''
        ctx.add_key("config.json", "example", 1)

    def down(self, ctx: MigrationContext):
        '''Remove example key'''
        ctx.remove_key("config.json", "example")
```

### Helper Methods Reference

The `MigrationContext` provides helper methods that automatically handle subconfigs and ensure atomicity. These methods are the recommended way to write migrations.

**IMPORTANT:** These helpers always operate on ALL subconfigs in a family. This is by design - migration authors cannot predict what custom subconfigs end users have created (e.g., `config.test.json`, `config.dev.json`). The helpers ensure all configurations stay in sync.

#### `ctx.add_key(file_path, key, value, create_parents=True, expand_schema=True)`
Adds a key at the specified keypath. Raises `KeyError` if the key already exists or parent keys are missing and `create_parents` is False.

If `expand_schema=True` (default), operations on schema files affect all subconfigs in the family.

```python
def up(self, ctx: MigrationContext):
    # Add a top-level key to all subconfigs
    ctx.add_key("config.json", "new_field", "default_value")

    # Add a nested key (creates parent keys automatically)
    ctx.add_key("config.json", "section.subsection.field", 42)

    # Require parent keys to exist
    ctx.add_key("config.json", "existing.path.new_key", True, create_parents=False)

    # Add key via schema reference (affects all subconfigs by default)
    ctx.add_key("config.schema.json", "new_field", "value")

    # Add key only to schema file
    ctx.add_key("config.schema.json", "new_field", "value", expand_schema=False)
```

#### `ctx.overwrite_key(file_path, key, value, create_parents=True, expand_schema=True)`
Adds or overwrites a key at the specified keypath. Unlike `add_key`, this will not fail if the key already exists.

If `expand_schema=True` (default), operations on schema files affect all subconfigs in the family.

```python
def up(self, ctx: MigrationContext):
    # Update existing value or create if missing (affects all subconfigs)
    ctx.overwrite_key("config.json", "version", "2.0")

    # Update via schema reference (affects all subconfigs by default)
    ctx.overwrite_key("config.schema.json", "version", "2.0")
```

#### `ctx.remove_key(file_path, key, expand_schema=True)`
Removes a key at the specified keypath. If any part is not present, the key is considered already deleted (no error raised).

If `expand_schema=True` (default), operations on schema files affect all subconfigs in the family.

```python
def up(self, ctx: MigrationContext):
    # Remove a nested key from all subconfigs
    ctx.remove_key("config.json", "deprecated.old_field")

    # Remove via schema reference (affects all subconfigs by default)
    ctx.remove_key("config.schema.json", "deprecated.old_field")
```

#### `ctx.move_key(file_path, src, dst, expand_schema=True)`
Moves an object at a specified key to a new key. All intermediate keys must be present. Fails if the destination already exists.

If `expand_schema=True` (default), operations on schema files affect all subconfigs in the family.

```python
def up(self, ctx: MigrationContext):
    # Move a key to a new location (must be nested under an existing parent)
    ctx.move_key("config.json", "old_location.field", "new_location")

    # Move via schema reference (affects all subconfigs by default)
    ctx.move_key("config.schema.json", "old_location.field", "new_location")
```

#### `ctx.rename_key(file_path, src, name, expand_schema=True)`
Renames a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.

If `expand_schema=True` (default), operations on schema files affect all subconfigs in the family.

```python
def up(self, ctx: MigrationContext):
    # Rename a key (stays in same location, just changes the key name)
    ctx.rename_key("config.json", "old_field.old_name", "new_name")

    # Rename via schema reference (affects all subconfigs by default)
    ctx.rename_key("config.schema.json", "old_field.old_name", "new_name")
```

#### `ctx.configs(file_path, expand_schema=True)`
Returns a list of all config paths that match the reference. For custom configs, returns all matching subconfigs.

When `expand_schema=True` (default), schema paths return all subconfigs of the corresponding custom config family. When `expand_schema=False`, schema paths return only the schema file itself.

```python
def up(self, ctx: MigrationContext):
    # Get all subconfigs of config.json (e.g., config.json, config.test.json, etc.)
    all_configs = ctx.configs("config.json")

    # Get all subconfigs via schema reference (same result as above)
    all_configs = ctx.configs("config.schema.json")

    # Get only the schema file itself
    schema_only = ctx.configs("config.schema.json", expand_schema=False)

    # Process each config individually if needed
    for config_path in all_configs:
        with ctx.load_for_update(config_path) as content:
            # Custom logic per config
            content["modified"] = True
```

### Working with Subconfigs

**All helper methods ALWAYS operate on all subconfigs in a family.** This is a critical design decision: migration authors cannot predict what custom subconfigs end users have created (e.g., `config.test.json`, `config.dev.json`, `config.production.json`). The helpers automatically discover and update all subconfigs to keep configurations in sync.

For example, if you have `config.json`, `config.custom.json`, and `config.test.json`:

```python
def up(self, ctx: MigrationContext):
    # This ALWAYS adds the key to ALL subconfigs: config.json, config.custom.json, config.test.json
    # You cannot selectively update only some subconfigs - this ensures consistency
    ctx.add_key("config.json", "new_field", "value")
```

#### Schema Operations

By default, operations on schema files also affect all subconfigs in the family:

```python
def up(self, ctx: MigrationContext):
    # This affects ALL custom configs: config.json, config.custom.json, config.test.json, etc.
    ctx.add_key("config.schema.json", "new_field", "value")
```

The `expand_schema` parameter only controls whether schema file references expand to custom configs. It does NOT allow selective updating of subconfigs:

```python
def up(self, ctx: MigrationContext):
    # expand_schema=False means "only modify the schema file itself"
    # This is rarely needed - typically only for schema metadata that shouldn't propagate to configs
    ctx.add_key("config.schema.json", "new_field", "value", expand_schema=False)

    # This STILL affects all subconfigs - expand_schema only applies to schema file references
    ctx.add_key("config.json", "new_field", "value", expand_schema=False)
```

All helper methods (`add_key`, `overwrite_key`, `remove_key`, `move_key`, `rename_key`) support the `expand_schema` parameter, but it only affects schema file behavior, not subconfig expansion.

### Direct Content Manipulation

For complex transformations, load and modify content directly. The context loads data from JSON as a dictionary:

```python
def up(self, ctx: MigrationContext):
    with ctx.load_for_update("config.json") as content:
        # Read existing values
        old_value = content["path"]["to"]["key"]

        # Modify in-place
        content["path"]["to"]["key"] = old_value.replace("_", "-")

        # Add computed values
        content["computed"] = len(old_value)
```

### Migration Template

When you run `python -m migrations generate <name>`, a new migration file is created with this template:

```python
from migrations import *


class <name>(ConfigMigration):
    def up(self, ctx: MigrationContext):
        raise NotImplementedError("Migration logic not implemented.")

    def down(self, ctx: MigrationContext):
        # Implement the logic to revert the migration if necessary.
        # Raises IrreversibleMigration by default.
        raise IrreversibleMigration
```

Replace the `raise NotImplementedError` with your migration logic. If the migration cannot be reversed, leave `down()` as-is with `raise IrreversibleMigration`.

## Atomicity Guarantees

If using the helpers shown above, the migration system makes strong guarantees about atomicity -- ALL operations in a migration are guaranteed to complete else ALL operations fail.

Under the hood, the migration system uses a transaction manager that compiles all changes made by a migration. The changes are written to a temporary directory `migrations/migrate/.transaction`. Once all changes are complete, the transaction manager copies the transaction file to the reference path, overwriting the old configuration. Note that nested transactions are not supported.

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

## Working with Subconfigs

Subconfigs allow you to create multiple variations of a configuration that share the same schema. For example, you might have:

* `config.json` - Your main configuration
* `config.custom.json` - An alternate configuration for specific use cases
* `config.schema.json` - The schema definition

### Creating Subconfigs

```bash
# Create a subconfig (automatically infers reference from name)
python -m migrations subconfig config.custom.json

# Explicitly specify the reference config
python -m migrations subconfig config.custom.json --reference config.json
```

### Naming Convention

Subconfigs must follow the pattern `<name>.<subname>.json` where:
* `<name>` matches the base config name (e.g., `config`)
* `<subname>` is your custom identifier (e.g., `custom`, `dev`, `test`)
* The reference config `<name>.json` must exist
* The schema `<name>.schema.json` must exist

### Migration Behavior

Subconfigs are created by copying the reference config and inherit its complete migration state. This ensures:

* New subconfigs start at the same migration version as the reference
* All future migrations automatically apply to both the reference and subconfigs
* The migration system treats them as a family of related configurations

If a subconfig already exists with a different migration state, the `subconfig` command will abort to prevent data loss.

## CLI Reference

```bash
# Initialize configs from schemas
# This operation is idempotent
# (alias: i)
python -m migrations init

# Create a subconfiguration from a reference config
# Subconfigs inherit migration state from the reference
# (alias: s)
python -m migrations subconfig <name>.<subname>.json
python -m migrations subconfig <name>.<subname>.json --reference <name>.json

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

# Reset custom configurations (DESTRUCTIVE)
# Removes all custom config files and custom migration status
# Useful when custom subconfigs are out of sync with migrations
# (alias: r)
python -m migrations reset
```

## Troubleshooting

### Resetting Custom Configurations

If your custom configuration files get out of sync with the migration system, you can use the `reset` command to start fresh:

```bash
python -m migrations reset
```

**What this does:**
- Removes **all** custom configuration files (`config.json`, `coordinates/*.json`, `colors/*.json`, etc.)
- Deletes the `custom-status.json` file that tracks migration state for custom configs
- **Preserves** all schema files (`*.schema.json`) and the `schema-status.json`

**When to use this:**
- Custom subconfigs have divergent migration states and won't sync
- You want to start fresh with default configurations
- Migration errors have left your custom configs in an inconsistent state

**⚠️ Warning:** This is a **destructive operation**. Any customizations in your config files will be lost. The command will prompt for confirmation before proceeding.

**After reset:**
```bash
# Reinitialize configs from schemas
python -m migrations init

# Your configs will now be in sync with the current schema migration state
```

## Example Workflows

### Basic Migration Workflow

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

### Working with Subconfigs

```bash
# 1. Initialize main configs
python -m migrations init

# 2. Create a subconfig for testing
python -m migrations s config.test.json

# 3. Make changes to config.test.json as needed
# (edit the file manually)

# 4. Later, create a migration affecting all configs
python -m migrations g add_new_feature

# 5. In the migration, operations on "config.json" affect all subconfigs
# migrations/migrate/{timestamp}_add_new_feature.py:
#   def up(self, ctx: MigrationContext):
#       ctx.add_key("config.json", "new_feature", True)

# 6. Apply - this updates config.json AND config.test.json
python -m migrations up
```

### Recovering from Migration Issues

```bash
# Scenario: Custom configs are out of sync and migrations are failing

# 1. Reset all custom configurations (you'll be prompted to confirm)
python -m migrations reset

# 2. Reinitialize from schemas (creates fresh configs at current migration state)
python -m migrations init

# 3. Your configs are now in sync and ready to use
# Note: Any custom values in your old config files are lost - you'll need to
# re-apply your customizations manually
```
