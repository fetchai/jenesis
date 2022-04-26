import platform
from typing import Union, List

from haul.keyring.amino.codec import LocalInfo, OfflineInfo

try:
    from haul.keyring import macos
except Exception:
    pass


def query_keychain_item(name: str) -> Union[LocalInfo, OfflineInfo]:
    system = platform.system()
    if system == 'Darwin':
        return macos.query_keychain_item(name)

    raise RuntimeError(f'Platform {system} not currently supported')


def query_keychain_items() -> List[str]:
    system = platform.system()
    if system == 'Darwin':
        return macos.query_keychain_items()

    raise RuntimeError(f'Platform {system} not currently supported')
