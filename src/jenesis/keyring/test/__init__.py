from pathlib import Path
from typing import Dict, List, Union

from jwskate import JweCompact

from jenesis.keyring.amino.codec import LocalInfo, OfflineInfo
from jenesis.keyring.errors import KeychainError
from jenesis.keyring.linux import (
    query_keychain_item as linux_query_keychain_item,
)
from jenesis.keyring.linux import (
    query_keychain_items as linux_query_keychain_items,
)


class KeychainItem:
    DEFAULT_COSMOS_TEST_KEYRING_PASSWORD = "test"

    def __init__(self, filepath: Path):
        self._filepath = Path(filepath)

    def get_label(self) -> str:
        return self._filepath.name

    def get_secret(self):
        return JweCompact(self._filepath.read_bytes()).decrypt_with_password(
            self.DEFAULT_COSMOS_TEST_KEYRING_PASSWORD
        )


class Collection:
    def __init__(self, path: Path):
        self._path = path

    def get_all_items(self) -> List[KeychainItem]:
        return [KeychainItem(i) for i in self._path.iterdir() if i.is_file()]

    def search_items(self, query: Dict[str, str]) -> List[KeychainItem]:
        if "profile" not in query:
            raise TestKeychainError("only `profile` query supported")
        return [
            i
            for i in self.get_all_items()
            if i.get_label() == query["profile"]
        ]


class KeyringTestBackend:  # pylint: disable=too-few-public-methods
    dir = ".fetchd/keyring-test/"

    def get_preferred_collection(self) -> Collection:
        return Collection(Path.home() / self.dir)


class TestKeychainError(KeychainError):
    pass


def query_keychain_item(name: str) -> Union[LocalInfo, OfflineInfo]:
    return linux_query_keychain_item(
        name=name, keyring_class=KeyringTestBackend
    )


def query_keychain_items() -> List[str]:
    return linux_query_keychain_items(keyring_class=KeyringTestBackend)
