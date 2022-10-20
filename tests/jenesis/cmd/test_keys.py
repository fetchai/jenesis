import subprocess
import pytest
import random
import os
from tempfile import mkdtemp
import toml
from jenesis.config import Config

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")
    os.chdir(path)

    Config.create_project("project", profile, network)
    os.chdir(os.path.join(path, "project"))

    project_root = os.path.abspath(os.getcwd())

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(project_root, input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)


    # add init argument for deployment
    data["project"]["keyring_backend"] = "test"

    with open(toml_path, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)

    subprocess.run("fetchd config keyring-backend test", shell=True)

    key = "test_key_2"
    
    p = subprocess.run("fetchd keys add " + key, shell=True, capture_output=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == jenesis_key_address

    #shutil.rmtree(path)



