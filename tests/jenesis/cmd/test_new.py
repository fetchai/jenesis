import os
import shutil
import subprocess

import toml
from jenesis.config import Config
from jenesis.network import fetchai_testnet_config


def test_new_create_project():
    """Test project creation when (new) command is selected"""

    project_name = "ProjectX"
    network_name = "fetchai-testnet"
    Config.create_project(project_name, "testing", network_name)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), project_name, input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    assert data["project"]["name"] == project_name

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    network = {"name": ""}
    network.update(vars(fetchai_testnet_config()))

    assert data["project"]["authors"] == authors
    assert data["profile"]["testing"]["network"] == network
    shutil.rmtree(project_name)