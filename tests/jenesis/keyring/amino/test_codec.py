from io import BytesIO
import pytest

from haul.keyring.amino.codec import *

prefix_test_data = (
    ('0000000000000000000000000000000000000000000000000000000000000000', '00000000'),
    ('ffffff01020304ffffffffffffffffffffffffffffffffffffffffffffffffff', '01020304'),
    ('00ffffff01020304ffffffffffffffffffffffffffffffffffffffffffffffff', '01020304'),
    ('ffffff0001020304ffffffffffffffffffffffffffffffffffffffffffffffff', '01020304'),
    ('00ffffff0001020304ffffffffffffffffffffffffffffffffffffffffffffff', '01020304'),
)


@pytest.mark.parametrize("input,expected", prefix_test_data)
def test_prefix_computation(input, expected):
    prefix = compute_prefix(bytes.fromhex(input))
    assert prefix.hex() == expected


named_prefixes = (
    ('crypto/keys/BIP44Params', '3c58bbec'),
    ('crypto/keys/localInfo', '0dad153d'),
    ('crypto/keys/ledgerInfo', 'a08cb0fb'),
    ('crypto/keys/offlineInfo', '1f4d3ed6'),
    ('crypto/keys/multiInfo', '34878fb8'),
    ('tendermint/PrivKeySecp256k1', 'e1b0f79b'),
    ('tendermint/PubKeySecp256k1', 'eb5ae987'),
)


# tendermint/PrivKeySecp256k1

@pytest.mark.parametrize("input,expected", named_prefixes)
def test_named_prefix(input, expected):
    prefix = build_prefix_from_string(input)
    assert prefix.hex() == expected


uvarint_parse_cases = (
    (b'\x00\x00\x00\x00\x00', '0', 1),
    (b'\x80\x00', '0', 2),
    (b'\x72\x00', '0x72', 1),
    (b'\xFF\xFF\x7F', '0x1FFFFF', 3),
)


@pytest.mark.parametrize("input,expected,consumed_bytes", uvarint_parse_cases)
def test_uvarint_parsing(input, expected, consumed_bytes):
    data = BytesIO(input)
    value = parse_uvarint(data)

    assert value == int(expected, 0)
    assert data.tell() == consumed_bytes


def test_uvarint_parsing_underflow():
    with pytest.raises(CodecParseError):
        parse_uvarint(BytesIO(b''))

    with pytest.raises(CodecParseError):
        parse_uvarint(BytesIO(b'\x80'))


precached_prefixes = (
    ('crypto/keys/localInfo', LOCAL_INFO_PREFIX),
    ('crypto/keys/offlineInfo', OFFLINE_INFO_PREFIX),
    ('tendermint/PrivKeySecp256k1', PRIVATE_KEY_SECP256K1_PREFIX),
    ('tendermint/PubKeySecp256k1', PUBLIC_KEY_SECP256K1_PREFIX),
)


@pytest.mark.parametrize("text,prefix", precached_prefixes)
def test_validate_precached_prefixes(text, prefix):
    assert build_prefix_from_string(text) == prefix


def test_extract_bytes_normal():
    data = extract_bytes(BytesIO(b'\x01\x02\x03'), 2)
    assert data == b'\x01\x02'


def test_extract_bytes_underflow():
    with pytest.raises(CodecParseError):
        extract_bytes(BytesIO(b'\x01\x02\x03'), 4)


def test_extract_bytes_empty():
    with pytest.raises(CodecParseError):
        extract_bytes(BytesIO(b''), 1)


def test_extract_byte_normal():
    assert extract_byte(BytesIO(b'\x01')) == 0x01


def test_extract_byte_underflow():
    with pytest.raises(CodecParseError):
        extract_byte(BytesIO(b''))


fields_test_cases = (
    ('0a04DEADBEEF1202FFFF', (b'\xde\xad\xbe\xef', b'\xff\xff')),
    ('0a01011201021a0103220104', (b'\x01', b'\x02', b'\x03', b'\x04')),
)


@pytest.mark.parametrize("stream,expected_fields", fields_test_cases)
def test_unmarshal_fields(stream, expected_fields):
    actual_fields = list(unmarshal_fields(BytesIO(bytes.fromhex(stream))))

    assert len(actual_fields) == len(expected_fields)

    for n, ((field_idx, field), expected_field) in enumerate(zip(actual_fields, expected_fields)):
        assert n + 1 == field_idx
        assert field == expected_field


def test_unmarshal_fields_bad_field_type():
    with pytest.raises(CodecParseError):
        list(unmarshal_fields(BytesIO(b'\x0b')))


def test_unmarshall_public_key_success():
    d = 'eb5ae98721010203040506070809101112131415161718192021222324252627282930313233'
    public_key = unmarshal_public_key(BytesIO(bytes.fromhex(d)))
    assert public_key == b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33'


def test_unmarshall_public_key_bad_prefix():
    with pytest.raises(CodecParseError):
        unmarshal_public_key(BytesIO(bytes.fromhex('ffffffff')))


def test_unmarshall_public_key_bad_length():
    with pytest.raises(CodecParseError):
        unmarshal_public_key(BytesIO(bytes.fromhex('eb5ae98700')))


def test_unmarshall_private_key_success():
    d = 'e1b0f79b200102030405060708091011121314151617181920212223242526272829303132'
    public_key = unmarshal_private_key(BytesIO(bytes.fromhex(d)))
    assert public_key == b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32'


def test_unmarshall_private_key_bad_prefix():
    with pytest.raises(CodecParseError):
        unmarshal_private_key(BytesIO(bytes.fromhex('ffffffff')))


def test_unmarshall_private_key_bad_length():
    with pytest.raises(CodecParseError):
        unmarshal_private_key(BytesIO(bytes.fromhex('e1b0f79b00')))


def test_unmarshal_local_info_success():
    d = b'\x0a\x08key-name\x12\x26\xeb\x5a\xe9\x87\x21\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x1a\x25\xe1\xb0\xf7\x9b\x20\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x22\x04algo'

    local_info = unmarshal_local_info(BytesIO(d))
    assert local_info == LocalInfo(
        name='key-name',
        public_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33',
        private_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32',
        algorithm='algo',
    )


def test_unmarshal_local_info_bad_field():
    with pytest.raises(CodecParseError):
        unmarshal_local_info(BytesIO(b'\x42\x01\x00'))


def test_unmarshal_offline_info_success():
    d = b'\x0a\x08key-name\x12\x26\xeb\x5a\xe9\x87\x21\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x1a\x04algo'

    offline_info = unmarshal_offline_info(BytesIO(d))
    assert offline_info == OfflineInfo(
        name='key-name',
        public_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33',
        algorithm='algo',
    )


def test_unmarshal_offline_info_bad_field():
    with pytest.raises(CodecParseError):
        unmarshal_offline_info(BytesIO(b'\x42\x01\x00'))


binary_bare_test_cases = (
    (
        b'\x1f\x4d\x3e\xd6\x0a\x08key-name\x12\x26\xeb\x5a\xe9\x87\x21\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x1a\x04algo',
        OfflineInfo(
            name='key-name',
            public_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33',
            algorithm='algo',
        )
    ),
    (
        b'\x0d\xad\x15\x3d\x0a\x08key-name\x12\x26\xeb\x5a\xe9\x87\x21\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33\x1a\x25\xe1\xb0\xf7\x9b\x20\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x22\x04algo',
        LocalInfo(
            name='key-name',
            public_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32\x33',
            private_key=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x30\x31\x32',
            algorithm='algo',
        )
    ),
)


@pytest.mark.parametrize("stream,value", binary_bare_test_cases)
def test_unmarshal_binary_bare(stream, value):
    info = unmarshal_binary_bare(BytesIO(stream))
    assert info is not None
    assert info == value


def test_unmarshal_binary_bare_bad_prefix():
    assert unmarshal_binary_bare(BytesIO(b'\xff\xff\xff\xff')) is None


@pytest.mark.parametrize("stream,value", binary_bare_test_cases)
def test_unmarshal_binary_length_prefixed(stream, value):
    d = bytes([len(stream)]) + stream
    info = unmarshal_binary_length_prefixed(BytesIO(d))
    assert info is not None
    assert info == value
