import subprocess
import os
from tempfile import mkdtemp
import toml
from jenesis.config import Config



def test_keys():
    """Test key command"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")
    os.chdir(path)

    # create project
    Config.create_project("project", profile, network)
    os.chdir(os.path.join(path, "project"))

    project_root = os.path.abspath(os.getcwd())

    # read configuration file
    input_file_name = "jenesis.toml"
    toml_path = os.path.join(project_root, input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    # set Jenesis to test keyring backend
    data["project"]["keyring_backend"] = "test"

    with open(toml_path, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)

    # set fetchd to test keyring backend
    subprocess.run("fetchd config keyring-backend test", shell=True)

    key = "test_key"
    subprocess.run("fetchd keys add " + key, shell=True, capture_output=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)
    jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == jenesis_key_address

    #shutil.rmtree(path)



