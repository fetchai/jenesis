import os
import random
import shutil
import subprocess
import time
from tempfile import mkdtemp
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi

import pytest
import toml
from jenesis.config import Config


#@pytest.mark.skip
def test_deploy_run_contract():
    """Test deploy contract and run command"""

    # create first project and deploy a contract
    network = "fetchai-testnet"
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

    subprocess.run("fetchd keys add " + deployment_key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + deployment_key)

    faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())

    faucet_api.get_wealth(key_address)

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(os.getcwd(), input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

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
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    output_string = output.stdout.decode()

    start = 'jenesis run output:'
    end = '\nNetwork'

    result = output_string[output_string.find(start)+len(start):output_string.find(end)]

    assert result == "{'count': 8}"

    #shutil.rmtree(path)
