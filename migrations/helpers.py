import pathlib

from migrations.transaction import Transaction


SCHEMA_IDENTIFIER = "schema"

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

def configs(file_path: pathlib.Path, expand_schema: bool = True) -> list[pathlib.Path]:
    '''
    Returns all subconfigs that match the reference.

    For instance: 'config.sub.json' is a subconfig referencing the custom config 'config.json'.

    When expand_schema is True (default), schema paths return all subconfigs of the corresponding
    custom config family. When False, schema paths return only the schema file itself.

    Examples:
        configs("config.json") -> ["config.json", "config.test.json", "config.custom.json"]
        configs("config.schema.json", expand_schema=True) -> ["config.json", "config.test.json", ...]
        configs("config.schema.json", expand_schema=False) -> ["config.schema.json"]
    '''
    if not isinstance(file_path, pathlib.Path):
        file_path = pathlib.Path(file_path)

    # Handle schema files
    if SCHEMA_IDENTIFIER in file_path.name:
        if not expand_schema:
            return [file_path]

        # Convert schema path to custom config path and get its subconfigs
        # e.g., "config.schema.json" -> "config.json"
        custom_name = file_path.name.replace(f".{SCHEMA_IDENTIFIER}", "")
        custom_path = file_path.parent / custom_name
        file_path = custom_path

    # Get all subconfigs for the custom config
    parts = file_path.name.split(".")

    name = parts[0]
    ext = parts[-1]  # Use -1 instead of 1 to handle multi-part names like "config.test.json"
    directory = file_path.parents[0]

    output = []

    for path in directory.glob(f"*.{ext}"):
        if name not in path.name or SCHEMA_IDENTIFIER in path.name:
            continue

        output.append(path)

    return output

def add_key(txn: Transaction, file_path: pathlib.Path, key: str, value: any, create_parents: bool = True, expand_schema: bool = True):
    """
    Adds a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if the key already exists or parent keys are missing and `create_parents` is False.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.
    """
    for path in configs(file_path, expand_schema=expand_schema):
        _add_key(txn, path, key, value, create_parents)


def overwrite_key(txn: Transaction, file_path: pathlib.Path, key: str, value: any, create_parents: bool = True, expand_schema: bool = True):
    """
    Adds or overwrites a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if parent keys are missing and `create_parents` is False.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.
    """
    for path in configs(file_path, expand_schema=expand_schema):
        _add_key(txn, path, key, value, create_parents, overwrite=True)


def remove_key(txn: Transaction, file_path: pathlib.Path, key: str, expand_schema: bool = True):
    """
    Removes a key at the specified keypath. If any part is not present, the key is considered already deleted.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.
    """
    for path in configs(file_path, expand_schema=expand_schema):
        _remove_key(txn, path, key)

def move_key(txn: Transaction, file_path: pathlib.Path, src: str, dst: str, expand_schema: bool = True):
    """
    Moves an object at a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.

    If `expand_schema` is True (default), operations on schema files affect all subconfigs.
    """
    for path in configs(file_path, expand_schema=expand_schema):
        _move_key(txn, path, src, dst)

#### SINGLE-FILE HELPERS ####
# These encapsulate the functionality of the helpers above.
# They operate on single files, so they do not expand to relevant subconfigs and _usually_ should not be directly used.
def _add_key(
    txn: Transaction, file_path: pathlib.Path, key: str, value: any, create_parents: bool = True, overwrite: bool = False
):
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