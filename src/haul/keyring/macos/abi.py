# pylint: disable=C0103
from ctypes import c_void_p, CDLL, c_int32, c_uint32, c_int, c_char, byref
from ctypes.util import find_library

# Much of the following has been adapted from the keyring library on PyPi:
# https://github.com/jaraco/keyring/blob/3fe6695fabe6bdc7a4f0d72b1fea8f00d62067de/keyring/backends/macOS/api.py
_sec = CDLL(find_library('Security'))
_core = CDLL(find_library('CoreServices'))
_found = CDLL(find_library('Foundation'))

CFDictionaryCreate = _found.CFDictionaryCreate
CFDictionaryCreate.restype = c_void_p
CFDictionaryCreate.argtypes = (
    c_void_p,
    c_void_p,
    c_void_p,
    c_int32,
    c_void_p,
    c_void_p,
)

CFStringCreateWithCString = _found.CFStringCreateWithCString
CFStringCreateWithCString.restype = c_void_p
CFStringCreateWithCString.argtypes = (c_void_p, c_void_p, c_uint32)

CFNumberCreate = _found.CFNumberCreate
CFNumberCreate.restype = c_void_p
CFNumberCreate.argtypes = (c_void_p, c_uint32, c_void_p)

SecItemAdd = _sec.SecItemAdd
SecItemAdd.restype = c_int32
SecItemAdd.argtypes = (c_void_p, c_void_p)

SecItemCopyMatching = _sec.SecItemCopyMatching
SecItemCopyMatching.restype = c_int32
SecItemCopyMatching.argtypes = (c_void_p, c_void_p)

SecItemDelete = _sec.SecItemDelete
SecItemDelete.restype = c_int32
SecItemDelete.argtypes = (c_void_p,)

CFDataGetBytePtr = _found.CFDataGetBytePtr
CFDataGetBytePtr.restype = c_void_p
CFDataGetBytePtr.argtypes = (c_void_p,)

CFDataGetLength = _found.CFDataGetLength
CFDataGetLength.restype = c_int32
CFDataGetLength.argtypes = (c_void_p,)

CFArrayGetCount = _found.CFArrayGetCount
CFArrayGetCount.restype = c_int
CFArrayGetCount.argtypes = (c_void_p,)

CFArrayGetValueAtIndex = _found.CFArrayGetValueAtIndex
CFArrayGetValueAtIndex.restype = c_void_p
CFArrayGetValueAtIndex.argtypes = (c_void_p, c_int)

CFDictionaryGetCount = _found.CFDictionaryGetCount
CFDictionaryGetCount.restype = c_int
CFDictionaryGetCount.argtypes = (c_void_p,)

CFDictionaryGetKeysAndValues = _found.CFDictionaryGetKeysAndValues
CFDictionaryGetKeysAndValues.restype = c_void_p
CFDictionaryGetKeysAndValues.argtypes = (c_void_p, c_void_p, c_void_p)

CFDictionaryGetValue = _found.CFDictionaryGetValue
CFDictionaryGetValue.restype = c_void_p
CFDictionaryGetValue.argtypes = (c_void_p, c_void_p)

CFShow = _found.CFShow
CFShow.restype = c_void_p
CFShow.argtypes = (c_void_p,)

CFStringGetLength = _found.CFStringGetLength
CFStringGetLength.restype = c_int
CFStringGetLength.argtypes = (c_void_p,)

CFStringGetCStringPtr = _found.CFStringGetCStringPtr
CFStringGetCStringPtr.restype = c_int
CFStringGetCStringPtr.argtypes = (c_void_p, c_uint32)

CFStringGetCString = _found.CFStringGetCString
CFStringGetCString.restype = c_int
CFStringGetCString.argtypes = (c_void_p, c_void_p, c_int, c_uint32)

# String encodings
kCFStringEncodingASCII = 0x0600
kCFStringEncodingUTF8 = 0x08000100


def k_(s):
    return c_void_p.in_dll(_sec, s)


def create_cfbool(b: bool):
    return CFNumberCreate(None, 0x9, byref(c_int32(1 if b else 0)))  # int32


def create_cfstr(s: str):
    return CFStringCreateWithCString(
        None, s.encode('utf8'), kCFStringEncodingUTF8
    )


def get_cfstr_value(item: c_void_p) -> str:
    # determine the string length (and double it because CFStringGetCString requires extra space)
    buffer_len = CFStringGetLength(item) * 2

    # need to create a large string buffer here because otherwise this process can fail
    buffer = (c_char * buffer_len)()
    status = CFStringGetCString(item, byref(buffer), buffer_len, kCFStringEncodingUTF8)
    if status != 1:
        raise RuntimeError('Unable to get CFString value')

    return buffer.value.decode()
