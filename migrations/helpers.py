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

def configs(file_path: pathlib.Path) -> list[pathlib.Path]:
    '''
    Returns all subconfigs that match the reference. Schema paths return a single path since they do not support sub-schemas.

    For instance: 'config.sub.json' is a subconfig referencing the custom config 'config.json'.
    '''
    if not isinstance(file_path, pathlib.Path):
        file_path = pathlib.Path(file_path)

    if SCHEMA_IDENTIFIER in file_path.name:
        return [file_path]
    
    parts = file_path.name.split(".")

    name = parts[0]
    ext = parts[1]
    directory = file_path.parents[0]

    output = []

    for path in directory.glob(f"*.{ext}"):
        if name not in path.name or SCHEMA_IDENTIFIER in path.name:
            continue
            
        output.append(path)

    return output

def add_key(txn: Transaction, file_path: pathlib.Path, key: str, value: any, create_parents: bool = True):
    """
    Adds a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if the key already exists or parent keys are missing and `create_parents` is False.
    """
    for path in configs(file_path):
        _add_key(txn, path, key, value, create_parents)


def overwrite_key(txn: Transaction, file_path: pathlib.Path, key: str, value: any, create_parents: bool = True):
    """
    Adds or overwrites a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if parent keys are missing and `create_parents` is False.
    """
    for path in configs(file_path):
        _add_key(txn, path, key, value, create_parents, overwrite=True)


def remove_key(txn: Transaction, file_path: pathlib.Path, key: str):
    """
    Removes a key at the specified keypath. If any part is not present, the key is considered already deleted.
    """
    for path in configs(file_path):
        _remove_key(txn, path, key)

def move_key(txn: Transaction, file_path: pathlib.Path, src: str, dst: str):
    """
    Moves an object at a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.
    """
    for path in configs(file_path):
        _move_key(txn, path, src, dst)

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