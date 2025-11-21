import inspect, pathlib

from functools import wraps
from migrations.exceptions import *
from migrations.transaction import Transaction
from migrations.mode import MigrationMode

class Keypath:
    def __init__(self, keypath):
        self.keypath = keypath
        self.parts = keypath.split('.')

def cast_keypaths(*arg_names):
    """Decorator that casts specific named arguments to Keypath if they are strings."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = inspect.signature(func).bind(*args, **kwargs)
            bound.apply_defaults()

            for name in arg_names:
                if name in bound.arguments and isinstance(bound.arguments[name], str):
                    bound.arguments[name] = Keypath(bound.arguments[name])

            return func(*bound.args, **bound.kwargs)
        return wrapper
    return decorator

class ConfigMigration:
    '''Base class for configuration migrations.'''
    def __init__(self, version):
        self.version = version

        # Accessors for the MigrationManager
        self._targets = []
        self._mode = None

    def up(self):
        '''
        Performs a data migration for a configuration object.
        '''
        raise NotImplementedError("ConfigMigration subclasses must implement up()")

    def down(self):
        '''
        Reverse a migration. 

        Raises IrreversibleMigration if migration cannot be reversed.
        Default implementation assumes an irreversible migration.
        '''
        raise IrreversibleMigration()
    
    def _execute(self):
        if self._mode == MigrationMode.DOWN:
            return self.down()
        
        if self._mode == MigrationMode.UP:
            return self.up()

    @cast_keypaths("keypath")
    def add_key(self, keypath, value, configs):
        '''Add a key to the configuration at the specified keypath.'''
        for content in self.__enumerate_configs(configs):
            parts = keypath.parts
            current = content

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            if parts[-1] in current:
                raise KeyError(f"Keypath '{keypath.keypath}' already exists.")

            current[parts[-1]] = value

    @cast_keypaths("keypath")
    def remove_key(self, keypath, configs):
        '''Remove a key from the configuration at the specified keypath.'''
        for content in self.__enumerate_configs(configs):
            parts = keypath.parts
            current = content

            for part in parts[:-1]:
                if part not in current:
                    return

                current = current[part]

            del current[parts[-1]]

    @cast_keypaths("keypath_from", "keypath_to")
    def move_key(self, keypath_from, keypath_to, configs):
        '''Move a key from one keypath to another.'''
        for content in self.__enumerate_configs(configs):
            parts_from = keypath_from.parts
            parts_to = keypath_to.parts

            current_from = content
            for part in parts_from[:-1]:
                if part not in current_from:
                    raise KeyError(f"Keypath '{keypath_from.keypath}' does not exist.")

                current_from = current_from[part]

            if parts_from[-1] not in current_from:
                raise KeyError(f"Keypath '{keypath_from.keypath}' does not exist.")

            value = current_from[parts_from[-1]]
            del current_from[parts_from[-1]]

            current_to = content
            for part in parts_to[:-1]:
                if part not in current_to:
                    current_to[part] = {}
                current_to = current_to[part]

            current_to[parts_to[-1]] = value

    @cast_keypaths("keypath")
    def rename_key(self, keypath, new_name, configs):
        '''Rename a key at the specified keypath.'''
        for content in self.__enumerate_configs(configs):
            parts = keypath.parts
            current = content

            for part in parts[:-1]:
                if part not in current:
                    return

                current = current[part]

            if parts[-1] not in current:
                raise KeyError(f"Keypath '{keypath.keypath}' does not exist.")

            value = current[parts[-1]]
            del current[parts[-1]]
            current[new_name] = value

    def __enumerate_configs(self, configs):
        '''
        Iterate over all configuration files in the provided configs.
        Yields the JSON content of each configuration file, and writes back any changes.
        Uses self._mode to determine whether to add or remove migration from _migrations array.
        '''
        if not isinstance(configs, list):
            configs = [configs]

        paths = [pathlib.Path(config).absolute() for config in configs]

        with Transaction(self.version, mode=self._mode) as transaction:
            for path in paths:
                if path not in self._targets:
                    continue

                content = transaction.read(path)

                yield content

                transaction.write(path, content)

            for path in self._targets:
                if path in paths:
                    continue

                # Touch the file to update the version
                transaction.write(path, transaction.read(path))
