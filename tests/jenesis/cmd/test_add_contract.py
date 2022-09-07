import os
import shutil

import toml
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts

def test_add_contract():
    """Test adding new contracts"""

    network = "fetchai-testnet"
    profiles = ["profile_1", "profile_2", "profile_3"]

    path = os.getcwd()

    Config.create_project(path, profiles[0], network)
    Config.add_profile(path, profiles[1], network)

    template = "starter"
    contract_name = "test_contract"

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(contract_root, template, contract_name, None)

    contracts = detect_contracts(project_root)
    contract = contracts[0]

    Config.update_project(os.getcwd(), profiles[0], network, contract)
    Config.update_project(os.getcwd(), profiles[1], network, contract)

    Config.add_profile(path, profiles[2], network)

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(os.getcwd(), input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    profile_list = list(data["profile"].keys())

    for (i, profile) in enumerate(profiles):
        assert profile_list[i] == profile
        contract_data = data["profile"][profile]["contracts"][contract_name]
        contract_data =  data["profile"][profile]["contracts"][contract_name]
        assert contract_data["contract"] == contract_name
        assert contract_data["network"] == network
        assert contract_data["deployer_key"] == ""
        assert contract_data["init"]["count"] == ""

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")