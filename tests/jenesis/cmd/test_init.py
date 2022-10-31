import os
import shutil
import subprocess
from tempfile import mkdtemp

import toml
from jenesis.config import Config
from jenesis.network import fetchai_testnet_config



def test_init_create_project():
    """Test project creation when (init) command is selected"""

    # create the temporary clone folder
    temp_clone_path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    network_name = "fetchai-testnet"
    Config.create_project(temp_clone_path, "testing", network_name)

    input_file_name = "jenesis.toml"
    path = os.path.join(temp_clone_path, input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    assert data["project"]["name"] == os.path.basename(temp_clone_path)

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    network = {"name": ""}
    network.update(vars(fetchai_testnet_config()))

    assert data["project"]["authors"] == authors
    assert data["profile"]["testing"]["network"] == network

    # clean up the temporary folder
    #shutil.rmtree(temp_clone_path)