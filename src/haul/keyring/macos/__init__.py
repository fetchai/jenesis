from ctypes import c_void_p, byref, string_at
from io import BytesIO
from typing import List, Union

from haul.keyring.amino.codec import LocalInfo, OfflineInfo, unmarshal_binary_length_prefixed
from haul.keyring.macos.abi import CFDictionaryCreate, _found, k_, create_cfstr, create_cfbool, SecItemCopyMatching, \
    CFArrayGetCount, CFArrayGetValueAtIndex, CFStringGetLength, CFStringGetCString, CFDictionaryGetValue, CFShow, \
    get_cfstr_value, CFDataGetBytePtr, CFDataGetLength


class MacOsKeychainError(RuntimeError):
    pass


def _create_query(**kwargs):
    return CFDictionaryCreate(
        None,
        (c_void_p * len(kwargs))(*[k_(k) for k in kwargs]),
        (c_void_p * len(kwargs))(
            *[create_cfstr(v) if isinstance(v, str) else v for v in kwargs.values()]
        ),
        len(kwargs),
        _found.kCFTypeDictionaryKeyCallBacks,
        _found.kCFTypeDictionaryValueCallBacks,
    )


def query_keychain_item(name: str) -> Union[LocalInfo, OfflineInfo]:
    query = _create_query(
        kSecClass=k_('kSecClassGenericPassword'),
        kSecMatchLimit=k_('kSecMatchLimitOne'),
        kSecAttrService='fetch',
        kSecAttrAccount=f'{name}.info',
        kSecReturnData=create_cfbool(True),
    )

    data = c_void_p()
    status = SecItemCopyMatching(query, byref(data))

    if status != 0:
        raise MacOsKeychainError('Unable to query keyring items')

    buffer = BytesIO(string_at(CFDataGetBytePtr(data), CFDataGetLength(data)))
    info = unmarshal_binary_length_prefixed(buffer)
    if info is None:
        raise MacOsKeychainError('Unable to parse stored entry')

    return info


def query_keychain_items() -> List[str]:
    query = _create_query(
        kSecClass=k_('kSecClassGenericPassword'),
        kSecMatchLimit=k_('kSecMatchLimitAll'),
        kSecReturnAttributes=create_cfbool(True),
        kSecAttrService='fetch',
    )

    data = c_void_p()
    status = SecItemCopyMatching(query, byref(data))

    if status != 0:
        raise MacOsKeychainError('Unable to query keyring items')

    key_names = []

    # iterate over all the items
    for idx in range(CFArrayGetCount(data)):

        # lookup the CFDictionary at the given index
        val = CFArrayGetValueAtIndex(data, idx)

        # attempt to find the account ('acct') field for each item
        item = CFDictionaryGetValue(val, create_cfstr('acct'))

        # skip all items that don't have an acct field
        if item == 0:
            continue

        account = get_cfstr_value(item)
        if account.endswith('.info'):
            key_names.append(account[:-5])

    return list(set(key_names))
