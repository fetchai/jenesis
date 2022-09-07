import os
import shutil
import subprocess

import toml
from jenesis.config import Config
from jenesis.network import fetchai_testnet_config

def test_init_create_project():
    """Test project creation when (init) command is selected"""

    network_name = "fetchai-testnet"
    Config.create_project(os.getcwd(), "testing", network_name)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    assert data["project"]["name"] == os.path.basename(os.getcwd())

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    network = {"name": ""}
    network.update(vars(fetchai_testnet_config()))

    assert data["project"]["authors"] == authors
    assert data["profile"]["testing"]["network"] == network

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")