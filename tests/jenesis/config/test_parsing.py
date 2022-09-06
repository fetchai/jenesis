import os
import shutil
import subprocess
import time

import pytest
import toml
from jenesis.config import Config, ConfigurationError
from jenesis.contracts.detect import detect_contracts
from jenesis.network import fetchai_testnet_config



fail_parse_cases = (
    ({}, {}, r"unable to extract configuration string project\.name"),
    (
        {"project": {"name": ""}},
        {},
        r"unable to extract configuration string project\.authors",
    ),
)


@pytest.mark.skip
@pytest.mark.parametrize("config_contents, lock_contents, err_msg", fail_parse_cases)
def test_prefix_computation(config_contents, lock_contents, err_msg):
    with pytest.raises(ConfigurationError, match=err_msg):
        Config._loads(config_contents, lock_contents)

