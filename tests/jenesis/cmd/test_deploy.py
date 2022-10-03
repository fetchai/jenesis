import os
import shutil
import subprocess
import pytest
import time
from tempfile import mkdtemp

import toml
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts
from jenesis.network import fetchai_localnode_config
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract

@pytest.mark.skip
def test_deploy_contract():
    """Test deploy contract"""

    network = "fetchai-localnode"

    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")
    os.chdir(path)

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())

    Config.add_contract(project_root, template, contract_name, None)

    contracts = detect_contracts(project_root)
    contract = contracts[0]

    Config.update_project(os.getcwd(), profile, network, contract)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    deployment_key = "zzzz" # Chance mejor un random string

    subprocess.run("fetchd keys add " + deployment_key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + deployment_key)

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(os.getcwd(), input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    data["profile"][profile]["network"]["genesis_accounts"].append(key_address)
    data["profile"][profile]["contracts"][contract_name]["init"]["count"] = 5

    project_configuration_file = os.path.join(project_root, "jenesis.toml")

    with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)


    subprocess.run('jenesis deploy ' + deployment_key, shell = True)

    ledger = LedgerClient( fetchai_localnode_config())
    lock_file_path = os.path.join(project_root, "jenesis.lock")

    assert os.path.isfile(lock_file_path)

    lock_file_contents = toml.load(lock_file_path)
    contract_address = lock_file_contents["profile"][profile][contract_name]["address"]

    contract = LedgerContract(path=None, client=ledger, address=contract_address)

    assert contract.query({"get_count":{}}) == {'count': 5}

    # clean up the temporary folder
    #shutil.rmtree(path)