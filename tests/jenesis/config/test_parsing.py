import os
import shutil
import subprocess

import pytest
import toml
from jenesis.config import Config, ConfigurationError

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


def test_new_create_project():
    """Test project creation when (new) command is selected"""

    project_name = "ProjectX"
    network = "fetchai-testnet"
    Config.create_project(project_name, "testing", network)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), project_name, input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        toml_dict = toml.load(toml_file)

    assert toml_dict["project"]["name"] == project_name

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    assert toml_dict["project"]["authors"] == authors
    assert toml_dict["profile"]["testing"]["network"] == network
    shutil.rmtree(project_name)


def test_init_create_project():
    """Test project creation when (init) command is selected"""

    network = "fetchai-testnet"
    Config.create_project(os.getcwd(), "testing", network)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        toml_dict = toml.load(toml_file)

    assert toml_dict["project"]["name"] == os.path.basename(os.getcwd())

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    assert toml_dict["project"]["authors"] == authors
    assert toml_dict["profile"]["testing"]["network"] == network

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")
