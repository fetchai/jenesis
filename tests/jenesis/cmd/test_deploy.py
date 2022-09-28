import os
import shutil
import subprocess

import toml
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts


# Unfinished
def test_deploy_contract():
    """Test deploy contract"""

    network = "fetchai-localnode"
    profile = "profile_1"

    path = os.getcwd()

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())

    Config.add_contract(project_root, template, contract_name, None)

    contracts = detect_contracts(project_root)
    contract = contracts[0]

    Config.update_project(os.getcwd(), profile, network, contract)

    subprocess.run("jenesis compile", shell=True)

    deployment_key = "test_key"

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

    # Requires password:
    # subprocess.run('jenesis alpha deploy ' + deployment_key, shell = True)

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")