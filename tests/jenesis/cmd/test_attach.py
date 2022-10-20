import os
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
def test_attach():
    """Test attach contract"""

    # create first project and deploy a contract
    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    os.chdir(path)

    # create project
    Config.create_project("project_1", profile, network)
    os.chdir(os.path.join(path, "project_1"))

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())

    # add starter contract and update
    contract = Config.add_contract(project_root, template, contract_name, None)
    Config.update_project(os.getcwd(), profile, network, contract)

    # compile contract and wait for it to finish
    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(os.getcwd(), input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    # set contract init parameter
    data["profile"][profile]["contracts"][contract_name]["init"]["count"] = 5

    # set Jenesis to test keyring backend
    data["project"]["keyring_backend"] = "test"

    project_configuration_file = os.path.join(project_root, "jenesis.toml")

    with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)

    # add key
    deployment_key = "test_key"
    subprocess.run("fetchd keys add " + deployment_key, shell=True)

    # add funds to key
    key_address = subprocess.getoutput("fetchd keys show -a " + deployment_key)
    faucet = FaucetApi(NetworkConfig.fetchai_stable_testnet())
    faucet.get_wealth(key_address)

    # deploy using key
    subprocess.run('jenesis deploy ' + deployment_key, shell = True)

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

    # add contract and update
    contract = Config.add_contract(project_root, template, contract_name, None)
    Config.update_project(os.getcwd(), profile, network, contract)

    # compile contract and wait for it to finish
    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    # attach previously deployed contract
    subprocess.run(
        "jenesis attach " + contract_name + " " + contract_address, shell=True
    )

    file_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(file_path, "scripts/query_contract.py")

    # run scipt
    output = subprocess.run(
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    # get script output
    output_string = output.stdout.decode()
    start = 'jenesis run output:'
    result = output_string[output_string.find(start)+len(start):].replace("\n", "")

    assert result == "{'count': 5}"

    #shutil.rmtree(path)
