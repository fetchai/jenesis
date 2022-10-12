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

    file_path = os.path.dirname(os.path.realpath(__file__))

    script_path = os.path.join(file_path, "scripts/deploy_contract.py")

    subprocess.run("jenesis run " + script_path, shell=True)

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

    script_path = os.path.join(file_path, "scripts/query_contract.py")

    output = subprocess.run(
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    output_string = output.stdout.decode()

    start = 'jenesis run output:'

    result = output_string[output_string.find(start)+len(start):].replace("\n", "")

    assert result == "{'count': 8}"

    #shutil.rmtree(path)
