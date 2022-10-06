import os
import random
import shutil
import subprocess
import time
from tempfile import mkdtemp

import pytest
import toml
from jenesis.config import Config


#@pytest.mark.skip
def test_run_contract():
    """Test run contract"""

    # create first project and deploy a contract
    network = "fetchai-localnode"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    os.chdir(path)

    Config.create_project("project_1", profile, network)
    os.chdir(os.path.join(path, "project_1"))

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())

    contract = Config.add_contract(project_root, template, contract_name, None)

    Config.update_project(os.getcwd(), profile, network, contract)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    deployment_key = "test_key"
    # letters = 'abcdefghijklmnopqrstuvwxyz'
    # deployment_key = ''.join(random.choice(letters) for i in range(10))

    subprocess.run("fetchd keys add " + deployment_key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + deployment_key)

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(os.getcwd(), input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    # add key address to genesis accounts
    data["profile"][profile]["network"]["genesis_accounts"].append(key_address)

    # add init argument for deployment
    data["profile"][profile]["contracts"][contract_name]["init"]["count"] = 5

    project_configuration_file = os.path.join(project_root, "jenesis.toml")

    with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)

    subprocess.run("jenesis deploy " + deployment_key, shell=True)

    # get deployed contract address
    lock_file_path = os.path.join(project_root, "jenesis.lock")

    assert os.path.isfile(lock_file_path)

    lock_file_contents = toml.load(lock_file_path)
    contract_address = lock_file_contents["profile"][profile][contract_name]["address"]

    # create a second project and attach the deployed contract
    profile = "profile_2"

    os.chdir(path)

    Config.create_project("project_2", profile, network)
    os.chdir(os.path.join(path, "project_2"))

    project_root = os.path.abspath(os.getcwd())

    contract = Config.add_contract(project_root, template, contract_name, None)

    Config.update_project(os.getcwd(), profile, network, contract)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    subprocess.run(
        "jenesis attach " + contract_name + " " + contract_address, shell=True
    )

    file_path = os.path.dirname(os.path.realpath(__file__))

    script_path = os.path.join(file_path, "scripts/script.py")

    output = subprocess.run(
        "jenesis run " + script_path, shell=True, capture_output=True
    )

    output_string = output.stdout.decode()

    split_word = "jenesis run output:"

    # Get String after substring occurrence
    result = output_string.split(split_word, 1)[1].replace("\n", "")
    assert result == "{'count': 5}"

    #shutil.rmtree(path)
