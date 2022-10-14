from pathlib import Path
from unittest.mock import patch

from jenesis.keyring.test import query_keychain_item, query_keychain_items


def test_query_items():
    with patch(
        "jenesis.keyring.test.KeyringTestBackend.dir",
        str(Path(__file__).parent / "data"),
    ):
        assert set(query_keychain_items()) == set(["alice", "bob"])


def test_query_item():
    with patch(
        "jenesis.keyring.test.KeyringTestBackend.dir",
        str(Path(__file__).parent / "data"),
    ):
        assert query_keychain_item("bob").name == "bob"
