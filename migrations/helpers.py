from migrations.transaction import Transaction


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


def add_key(txn: Transaction, file_path: str, key: str, value: any, create_parents: bool = True):
    """
    Adds a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if the key already exists or parent keys are missing and `create_parents` is False.
    """
    _add_key(txn, file_path, key, value, create_parents)


def overwrite_key(txn: Transaction, file_path: str, key: str, value: any, create_parents: bool = True):
    """
    Adds or overwrites a key at the specified keypath. If `create_parents` is True, any missing keys along the path will be created.

    Raises KeyError if parent keys are missing and `create_parents` is False.
    """
    _add_key(txn, file_path, key, value, create_parents, overwrite=True)


def remove_key(txn: Transaction, file_path: str, key: str):
    """
    Removes a key at the specified keypath. If any part is not present, the key is considered already deleted.
    """
    keypath = Keypath(key)

    with txn.load_for_update(file_path) as content:
        target = content

        for part in keypath.parts[:-1]:
            if part not in target:
                return

            target = target[part]

        if keypath.parts[-1] in target:
            del target[keypath.parts[-1]]


def move_key(txn: Transaction, file_path: str, src: str, dst: str):
    """
    Moves an object at a specified key to a new key. All intermediate keys must be present. Fails if the value already exists.
    """
    src_keypath = Keypath(src)
    dst_keypath = Keypath(dst)

    key = None
    value = None

    with txn.load_for_update(file_path) as content:
        target = content

        for part in src_keypath.parts[:-1]:
            if part not in target:
                raise KeyError(f"Source keypath '{src_keypath}' does not exist")

            target = target[part]

        if src_keypath.parts[-1] in target:
            key = src_keypath.parts[-1]
            value = target[src_keypath.parts[-1]]

            del target[src_keypath.parts[-1]]

        if key is None:
            raise KeyError(f"Source keypath '{src_keypath}' does not exist")

        target = content

        for part in dst_keypath.parts:
            if part not in target:
                raise KeyError(f"Destination keypath '{dst_keypath}' does not exist")

            target = target[part]

        target[key] = value


def _add_key(
    txn: Transaction, file_path: str, key: str, value: any, create_parents: bool = True, overwrite: bool = False
):
    keypath = Keypath(key)

    with txn.load_for_update(file_path) as content:
        target = content

        for part in keypath.parts[:-1]:
            if part not in target:
                if create_parents == False:
                    raise KeyError(f"Keypath '{keypath}' does not exist")

                else:
                    target[part] = {}

            target = target[part]

        if keypath.parts[-1] in target and not overwrite:
            raise KeyError(f"Keypath '{keypath}' already exists")

        target[keypath.parts[-1]] = value
