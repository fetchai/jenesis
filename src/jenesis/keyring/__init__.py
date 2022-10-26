import platform
from typing import List, Union

from jenesis.keyring.amino.codec import LocalInfo, OfflineInfo
from jenesis.keyring import test

try:
    from jenesis.keyring import macos
except Exception:
    pass


try:
    from jenesis.keyring import linux
except Exception:
    pass


def query_keychain_item(name: str, backend: str = "os") -> Union[LocalInfo, OfflineInfo]:
    if backend == "os":
        system = platform.system()
        if system == "Darwin":
            return macos.query_keychain_item(name)

        if system == "Linux":
            return linux.query_keychain_item(name)

        raise RuntimeError(f"Platform {system} not currently supported")

    if backend == "test":
        return test.query_keychain_item(name)

    raise RuntimeError(f"Keyring backend '{backend}' not currently supported")


def query_keychain_items(backend: str = "os") -> List[str]:
    if backend == "os":
        system = platform.system()
        if system == "Darwin":
            return macos.query_keychain_items()

        if system == "Linux":
            return linux.query_keychain_items()

        raise RuntimeError(f"Platform {system} not currently supported")

    if backend == "test":
        return test.query_keychain_items()

    raise RuntimeError(f"Keyring backend '{backend}' not currently supported")
