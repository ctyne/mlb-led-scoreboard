"""
Migration execution context.

Provides a unified interface for migration operations, combining transaction management
with helper methods for config file manipulation.
"""

import pathlib
from typing import Any, Optional
from contextlib import contextmanager

from migrations.transaction import Transaction


# Constants
SCHEMA_IDENTIFIER = "schema"
IGNORE_LIST = ["emulator_config.json"]


class Keypath:
    """
    Converts a keypath string into a Keypath object by splitting on SEP.
    """

    SEP = "."

    def __init__(self, keypath_str: str):
        self.raw = keypath_str
        self.parts = keypath_str.split(Keypath.SEP)

    def __str__(self):
        return Keypath.SEP.join(self.parts)

    def __repr__(self):
        return self.__str__()


class MigrationContext:
    """
    Context for migration execution that combines transaction and helper methods.

    Provides a clean API for migrations by:
    - Managing the transaction lifecycle
    - Shadowing transaction methods (read, write, load_for_update)
    - Providing helper methods (add_key, remove_key, etc.) that automatically filter by target_files

    Usage:
        with MigrationContext(target_files=[...]) as ctx:
            ctx.add_key("config.json", "foo", "bar")
            with ctx.load_for_update("config.json") as content:
                content["key"] = "value"
    """

    def __init__(self, target_files: Optional[list[pathlib.Path]] = None):
        self.target_files = set(target_files) if target_files else None
        self._txn: Optional[Transaction] = None

    def __enter__(self):
        self._txn = Transaction()
        self._txn.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._txn:
            return self._txn.__exit__(exc_type, exc_value, traceback)
        return False

    # Transaction method shadows
    def read(self, path: pathlib.Path) -> dict:
        """Read a file within the transaction."""
        return self._txn.read(path)

    def write(self, path: pathlib.Path, data: dict) -> None:
        """Write to a file within the transaction."""
        self._txn.write(path, data)

    @contextmanager
    def load_for_update(self, file_path: pathlib.Path):
        """Load a file for update within the transaction."""
        with self._txn.load_for_update(file_path) as content:
            yield content

    def get_modified_files(self) -> list[pathlib.Path]:
        """Get list of files modified in this transaction."""
        return self._txn.get_modified_files()

    # Config helper
    def configs(self, file_paths: list[pathlib.Path] | pathlib.Path, expand_schema: bool = True) -> list[pathlib.Path]:
        """
        Returns all subconfigs that match the reference, filtered by target_files.

        Automatically uses this context's target_files to filter results.
        """
        return configs(file_paths, expand_schema=expand_schema, ctx=self)

    # Key manipulation helpers
    def add_key(
        self,
        file_path: pathlib.Path,
        key: str,
        value: Any,
        create_parents: bool = True,
        expand_schema: bool = True,
    ) -> None:
        """
        Adds a key at the specified keypath.

        If `create_parents` is True, any missing keys along the path will be created.
        Raises KeyError if the key already exists or parent keys are missing and `create_parents` is False.
        If `expand_schema` is True (default), operations on schema files affect all subconfigs.
        """
        add_key(self._txn, file_path, key, value, create_parents, expand_schema, ctx=self)

    def overwrite_key(
        self,
        file_path: pathlib.Path,
        key: str,
        value: Any,
        create_parents: bool = True,
        expand_schema: bool = True,
    ) -> None:
        """
        Adds or overwrites a key at the specified keypath.

        Unlike add_key, this will not fail if the key already exists.
        If `expand_schema` is True (default), operations on schema files affect all subconfigs.
        """
        overwrite_key(self._txn, file_path, key, value, create_parents, expand_schema, ctx=self)

    def remove_key(
        self,
        file_path: pathlib.Path,
        key: str,
        expand_schema: bool = True,
    ) -> None:
        """
        Removes a key at the specified keypath.

        If any part is not present, the key is considered already deleted.
        If `expand_schema` is True (default), operations on schema files affect all subconfigs.
        """
        remove_key(self._txn, file_path, key, expand_schema, ctx=self)

    def move_key(
        self,
        file_path: pathlib.Path,
        src: str,
        dst: str,
        expand_schema: bool = True,
    ) -> None:
        """
        Moves an object at a specified key to a new key.

        All intermediate keys must be present. Fails if the value already exists.
        If `expand_schema` is True (default), operations on schema files affect all subconfigs.
        """
        move_key(self._txn, file_path, src, dst, expand_schema, ctx=self)

    def rename_key(
        self,
        file_path: pathlib.Path,
        src: str,
        name: str,
        expand_schema: bool = True,
    ) -> None:
        """
        Renames a specified key to a new key.

        All intermediate keys must be present. Fails if the value already exists.
        If `expand_schema` is True (default), operations on schema files affect all subconfigs.
        """
        rename_key(self._txn, file_path, src, name, expand_schema, ctx=self)


# Module-level helper functions
# These can be used standalone or through MigrationContext methods


def configs(
    file_paths: list[pathlib.Path] | pathlib.Path, expand_schema: bool = True, ctx: Optional[MigrationContext] = None
) -> list[pathlib.Path]:
    """
    Returns all subconfigs that match the reference.

    For instance: 'config.sub.json' is a subconfig referencing the custom config 'config.json'.

    When expand_schema is True (default), schema paths return all subconfigs of the corresponding
    custom config family. When False, schema paths return only the schema file itself.

    If ctx is provided with target_files, filters the results to only include those files.

    Examples:
        configs("config.json") -> ["config.json", "config.test.json", "config.custom.json"]
        configs("config.schema.json", expand_schema=True) -> ["config.json", "config.test.json", ...]
        configs("config.schema.json", expand_schema=False) -> ["config.schema.json"]
        configs("config.json", ctx=ctx) -> filtered to ctx.target_files
    """
    if not isinstance(file_paths, list):
        file_paths = [file_paths]

    output = []

    for path in file_paths:
        output.extend(_configs(path, expand_schema))

    # Filter to target_files if ctx is provided
    if ctx and ctx.target_files is not None:
        from migrations.manager import MigrationManager

        # Normalize all paths for comparison
        target_set = {MigrationManager.normalize_path(f) for f in ctx.target_files}
        output = [f for f in output if MigrationManager.normalize_path(f) in target_set]

    return output


def _configs(file_path: pathlib.Path, expand_schema: bool) -> list[pathlib.Path]:
    """Internal helper for expanding config paths."""
    if not isinstance(file_path, pathlib.Path):
        file_path = pathlib.Path(file_path)

    # By default, return ALL configs in the family
    # If the user specified the migration against a custom config, only expand to custom subconfigs and skip the schema
    skip_schema = False

    # Handle schema files
    if SCHEMA_IDENTIFIER in file_path.name:
        if not expand_schema:
            return [file_path]

        # Convert schema path to custom config path and get its subconfigs
        # e.g., "config.schema.json" -> "config.json"
        custom_name = file_path.name.replace(f".{SCHEMA_IDENTIFIER}", "")
        custom_path = file_path.parent / custom_name
        file_path = custom_path
    else:
        skip_schema = True

    parts = file_path.name.split(".")

    name = parts[0]
    ext = parts[-1]
    directory = file_path.parents[0]

    output = []

    for path in directory.glob(f"*.{ext}"):
        # Doesn't match config family
        if name not in path.name:
            continue
        # Didn't specify a schema to start, so migration wants ONLY custom configs
        if SCHEMA_IDENTIFIER in path.name and skip_schema:
            continue
        # Is in ignore list
        if path.name in IGNORE_LIST:
            continue

        output.append(path)

    return output


def add_key(
    txn: Transaction,
    file_path: pathlib.Path,
    key: str,
    value: Any,
    create_parents: bool = True,
    expand_schema: bool = True,
    ctx: Optional[MigrationContext] = None,
) -> None:
    """
    Adds a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if the key already exists or parent keys are missing and `create_parents` is False.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.

    If `ctx` is provided with target_files, only operates on those specific files.
    """
    for path in configs(file_path, expand_schema=expand_schema, ctx=ctx):
        _add_key(txn, path, key, value, create_parents)


def overwrite_key(
    txn: Transaction,
    file_path: pathlib.Path,
    key: str,
    value: Any,
    create_parents: bool = True,
    expand_schema: bool = True,
    ctx: Optional[MigrationContext] = None,
) -> None:
    """
    Adds or overwrites a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if parent keys are missing and `create_parents` is False.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.

    If `ctx` is provided with target_files, only operates on those specific files.
    """
    for path in configs(file_path, expand_schema=expand_schema, ctx=ctx):
        _add_key(txn, path, key, value, create_parents, overwrite=True)


def remove_key(
    txn: Transaction,
    file_path: pathlib.Path,
    key: str,
    expand_schema: bool = True,
    ctx: Optional[MigrationContext] = None,
) -> None:
    """
    Removes a key at the specified keypath. If any part is not present, the key is considered already deleted.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.

    If `ctx` is provided with target_files, only operates on those specific files.
    """
    for path in configs(file_path, expand_schema=expand_schema, ctx=ctx):
        _remove_key(txn, path, key)


def move_key(
    txn: Transaction,
    file_path: pathlib.Path,
    src: str,
    dst: str,
    expand_schema: bool = True,
    ctx: Optional[MigrationContext] = None,
) -> None:
    """
    Moves an object at a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.

    If `ctx` is provided with target_files, only operates on those specific files.
    """
    for path in configs(file_path, expand_schema=expand_schema, ctx=ctx):
        _move_key(txn, path, src, dst)


def rename_key(
    txn: Transaction,
    file_path: pathlib.Path,
    src: str,
    name: str,
    expand_schema: bool = True,
    ctx: Optional[MigrationContext] = None,
) -> None:
    """
    Renames a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.

    If `ctx` is provided with target_files, only operates on those specific files.
    """
    for path in configs(file_path, expand_schema=expand_schema, ctx=ctx):
        _rename_key(txn, path, src, name)


# Internal single-file helpers
# These encapsulate the functionality of the helpers above.
# They operate on single files, so they do not expand to relevant subconfigs and _usually_ should not be directly used.


def _add_key(
    txn: Transaction,
    file_path: pathlib.Path,
    key: str,
    value: any,
    create_parents: bool = True,
    overwrite: bool = False,
):
    """Internal helper to add a key to a single file."""
    keypath = Keypath(key)

    with txn.load_for_update(file_path) as content:
        target = content

        for part in keypath.parts[:-1]:
            if part not in target:
                if create_parents == False:
                    raise KeyError(f"<{file_path}> Keypath '{keypath}' does not exist")

                else:
                    target[part] = {}

            target = target[part]

        if keypath.parts[-1] in target and not overwrite:
            raise KeyError(f"<{file_path}> Keypath '{keypath}' already exists")

        target[keypath.parts[-1]] = value


def _remove_key(txn: Transaction, file_path: pathlib.Path, key: str):
    """Internal helper to remove a key from a single file."""
    keypath = Keypath(key)

    with txn.load_for_update(file_path) as content:
        target = content

        for part in keypath.parts[:-1]:
            if part not in target:
                return

            target = target[part]

        if keypath.parts[-1] in target:
            del target[keypath.parts[-1]]


def _move_key(txn: Transaction, file_path: pathlib.Path, src: str, dst: str):
    """Internal helper to move a key within a single file."""
    src_keypath = Keypath(src)
    dst_keypath = Keypath(dst)

    key = None
    value = None

    with txn.load_for_update(file_path) as content:
        target = content

        for part in src_keypath.parts[:-1]:
            if part not in target:
                raise KeyError(f"<{file_path}> Source keypath '{src_keypath}' does not exist")

            target = target[part]

        if src_keypath.parts[-1] in target:
            key = src_keypath.parts[-1]
            value = target[src_keypath.parts[-1]]

            del target[src_keypath.parts[-1]]

        if key is None:
            raise KeyError(f"<{file_path}> Source keypath '{src_keypath}' does not exist")

        target = content

        for part in dst_keypath.parts:
            if part not in target:
                raise KeyError(f"<{file_path}> Destination keypath '{dst_keypath}' does not exist")

            target = target[part]

        target[key] = value


def _rename_key(txn: Transaction, file_path: pathlib.Path, key: str, name):
    """Internal helper to rename a key within a single file."""
    keypath = Keypath(key)

    with txn.load_for_update(file_path) as content:
        target = content

        for part in keypath.parts[:-1]:
            if part not in target:
                return

            target = target[part]

        if name in target:
            raise KeyError(f"<{file_path}> Renamed key '{keypath}' -> '{name}' already exists")

        value = None
        if keypath.parts[-1] in target:
            value = target[keypath.parts[-1]]
            del target[keypath.parts[-1]]
        else:
            raise KeyError(f"<{file_path}> Destination keypath '{keypath}' does not exist")

        target[name] = value
