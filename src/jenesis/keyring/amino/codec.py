import hashlib
import io
from dataclasses import dataclass
from typing import IO, Union, Optional, Generator, Tuple

LOCAL_INFO_PREFIX = b'\x0d\xad\x15\x3d'  # = build_prefix_from_string('crypto/keys/localInfo')
OFFLINE_INFO_PREFIX = b'\x1f\x4d\x3e\xd6'  # = build_prefix_from_string('crypto/keys/offlineInfo')
PUBLIC_KEY_SECP256K1_PREFIX = b'\xeb\x5a\xe9\x87'  # = build_prefix_from_string('tendermint/PubKeySecp256k1')
PRIVATE_KEY_SECP256K1_PREFIX = b'\xe1\xb0\xf7\x9b'  # = build_prefix_from_string('tendermint/PrivKeySecp256k1')
PUBLIC_KEY_SECP256K1_LENGTH = 33
PRIVATE_KEY_SECP256K1_LENGTH = 32


@dataclass
class OfflineInfo:
    name: str
    public_key: bytes
    algorithm: str


@dataclass
class LocalInfo:
    name: str
    public_key: bytes
    private_key: bytes
    algorithm: str


class CodecParseError(RuntimeError):
    pass


def compute_prefix(data: bytes) -> bytes:
    assert len(data) == 32  # should match a sha256 digest

    if data[0] == 0:
        skip_length = 4
    else:
        skip_length = 3

    if data[skip_length] == 0:
        skip_length += 1

    return data[skip_length:skip_length + 4]


def build_prefix_from_string(name: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(name.encode())
    return compute_prefix(hasher.digest())


def parse_uvarint(data: IO[bytes]) -> int:
    value = 0
    while True:
        data_bytes = data.read(1)
        if len(data_bytes) == 0:
            raise CodecParseError('Reached the end of the binary stream')

        # add the bits to the value
        value = (value << 7) | (data_bytes[0] & 0x7F)

        # determine if there is a continuation mark on this byte
        if data_bytes[0] & 0x80 == 0:
            break

    return value


def extract_bytes(data: IO[bytes], length: int) -> bytes:
    value = data.read(length)
    if len(value) == 0:
        raise CodecParseError('reached the EOF prematurely during processing')
    if len(value) != length:
        raise CodecParseError(f'unable to read expected number of bytes (wanted: {length} received: {len(value)}')
    return value


def extract_byte(data: IO[bytes]) -> int:
    value = extract_bytes(data, 1)
    return value[0]


def unmarshal_fields(data: IO[bytes]) -> Generator[Tuple[int, bytes], None, None]:
    while True:
        prefix = data.read(1)
        if prefix == b'':
            break

        # extract the field and type
        field_index = (prefix[0] >> 3) & 0x1f
        field_type = prefix[0] & 0x7
        if field_type != 2:
            raise CodecParseError(f'unexpected field type {field_type}')

        # extract the length
        length = parse_uvarint(data)
        field_buffer = extract_bytes(data, length)

        yield field_index, field_buffer


def unmarshal_public_key(data: IO[bytes]) -> bytes:
    prefix = extract_bytes(data, 4)
    if prefix != PUBLIC_KEY_SECP256K1_PREFIX:
        raise CodecParseError(f'invalid public key prefix 0x{prefix.hex()}')

    length = parse_uvarint(data)
    if length != PUBLIC_KEY_SECP256K1_LENGTH:
        raise CodecParseError(f'invalid public key length {length}')

    return extract_bytes(data, length)


def unmarshal_private_key(data: IO[bytes]) -> bytes:
    prefix = extract_bytes(data, 4)
    if prefix != PRIVATE_KEY_SECP256K1_PREFIX:
        raise CodecParseError(f'invalid private key prefix 0x{prefix.hex()}')

    length = parse_uvarint(data)
    if length != PRIVATE_KEY_SECP256K1_LENGTH:
        raise CodecParseError(f'invalid private key length {length}')

    return extract_bytes(data, length)


def unmarshal_local_info(data: IO[bytes]) -> LocalInfo:
    parameters = {}

    for idx, field in unmarshal_fields(data):
        if idx == 1:
            parameters['name'] = field.decode()
        elif idx == 2:
            parameters['public_key'] = unmarshal_public_key(io.BytesIO(field))
        elif idx == 3:
            parameters['private_key'] = unmarshal_private_key(io.BytesIO(field))
        elif idx == 4:
            parameters['algorithm'] = field.decode()
        else:
            raise CodecParseError(f'unexpected field index {idx} for LocalInfo')

    return LocalInfo(**parameters)


def unmarshal_offline_info(data: IO[bytes]) -> OfflineInfo:
    parameters = {}

    for idx, field in unmarshal_fields(data):
        if idx == 1:
            parameters['name'] = field.decode()
        elif idx == 2:
            parameters['public_key'] = unmarshal_public_key(io.BytesIO(field))
        elif idx == 3:
            parameters['algorithm'] = field.decode()
        else:
            raise CodecParseError(f'unexpected field index {idx} for LocalInfo')

    return OfflineInfo(**parameters)


def unmarshal_binary_bare(data: IO[bytes]) -> Optional[Union[LocalInfo, OfflineInfo]]:
    prefix = extract_bytes(data, 4)
    if prefix == LOCAL_INFO_PREFIX:
        return unmarshal_local_info(data)
    if prefix == OFFLINE_INFO_PREFIX:
        return unmarshal_offline_info(data)

    return None


def unmarshal_binary_length_prefixed(data: IO[bytes]) -> Optional[Union[LocalInfo, OfflineInfo]]:
    length = parse_uvarint(data)
    raw_data = extract_bytes(data, length)

    # create a new buffer to be processed (we assume that it will be consumed)
    buffer = io.BytesIO(raw_data)
    return unmarshal_binary_bare(buffer)
