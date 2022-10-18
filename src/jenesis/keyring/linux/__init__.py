import json
from base64 import b64decode
from io import BytesIO
from typing import List, Union

from keyring.backends.SecretService import Keyring as BaseKeyring

from jenesis.keyring.amino.codec import (
    LocalInfo,
    OfflineInfo,
    unmarshal_binary_length_prefixed,
)
from jenesis.keyring.errors import KeychainError


class Keyring(BaseKeyring):
    preferred_collection = "/org/freedesktop/secrets/collection/fetch"


class LinuxKeychainError(KeychainError):
    pass


def query_keychain_item(name: str, keyring_class=Keyring) -> Union[LocalInfo, OfflineInfo]:
    keyring = keyring_class()
    collection = keyring.get_preferred_collection()
    items = list(collection.search_items({"profile": f"{name}.info"}))
    if not items:
        raise LinuxKeychainError("Key not found")

    item = items[0]
    try:
        data = json.loads(item.get_secret())
        binary_data = b64decode(data["Data"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise LinuxKeychainError("Unable to parse stored entry") from exc

    info = unmarshal_binary_length_prefixed(BytesIO(binary_data))
    if info is None:
        raise LinuxKeychainError("Unable to parse stored entry")
    return info


def query_keychain_items(keyring_class=Keyring) -> List[str]:
    keyring = keyring_class()
    collection = keyring.get_preferred_collection()
    items = list(collection.get_all_items())
    key_names = []
    for item in items:
        account = item.get_label()
        if account.endswith(".info"):
            key_names.append(account[:-5])

    return list(set(key_names))
