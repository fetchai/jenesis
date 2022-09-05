import os
import shutil
import subprocess
import time

import pytest
import toml
from jenesis.config import Config, ConfigurationError
from jenesis.contracts.detect import detect_contracts
from jenesis.network import fetchai_testnet_config



fail_parse_cases = (
    ({}, {}, r"unable to extract configuration string project\.name"),
    (
        {"project": {"name": ""}},
        {},
        r"unable to extract configuration string project\.authors",
    ),
)


@pytest.mark.skip
@pytest.mark.parametrize("config_contents, lock_contents, err_msg", fail_parse_cases)
def test_prefix_computation(config_contents, lock_contents, err_msg):
    with pytest.raises(ConfigurationError, match=err_msg):
        Config._loads(config_contents, lock_contents)


def test_new_create_project():
    """Test project creation when (new) command is selected"""

    project_name = "ProjectX"
    network_name = "fetchai-testnet"
    Config.create_project(project_name, "testing", network_name)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), project_name, input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    assert data["project"]["name"] == project_name

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    network = {"name": ""}
    network.update(vars(fetchai_testnet_config()))

    assert data["project"]["authors"] == authors
    assert data["profile"]["testing"]["network"] == network
    shutil.rmtree(project_name)


def test_init_create_project():
    """Test project creation when (init) command is selected"""

    network_name = "fetchai-testnet"
    Config.create_project(os.getcwd(), "testing", network_name)

    input_file_name = "jenesis.toml"
    path = os.path.join(os.getcwd(), input_file_name)
    with open(path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    assert data["project"]["name"] == os.path.basename(os.getcwd())

    user_name = subprocess.getoutput("git config user.name")
    user_email = subprocess.getoutput("git config user.email")
    authors = [f"{user_name} <{user_email}>"]

    network = {"name": ""}
    network.update(vars(fetchai_testnet_config()))

    assert data["project"]["authors"] == authors
    assert data["profile"]["testing"]["network"] == network

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")


def test_add_profile():
    """Test adding new profiles"""

    networks = ["fetchai-testnet", "fetchai-localnode"]
    chain_ids = ["dorado-1", "localnode"]
    profiles = ["profile_1", "profile_2", "profile_3", "profile_4"]

    path = os.getcwd()

    Config.create_project(path, profiles[0], networks[1])

    for (i, profile) in enumerate(profiles[1:]):
        Config.add_profile(path, profile, networks[i % 2])

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(path, input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    profile_list = list(data["profile"].keys())

    for (i, profile) in enumerate(profiles):
        assert profile_list[i] == profile
        assert data["profile"][profile]["network"]["name"] == networks[(i + 1) % 2]
        assert data["profile"][profile]["network"]["chain_id"] == chain_ids[(i + 1) % 2]

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")


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


def test_compile_contract():
    """Test compile contract"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = os.getcwd()

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(contract_root, template, contract_name, None)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(35)

    compiled_contract = os.path.join(
        contract_root, "artifacts", contract_name + ".wasm"
    )

    # check to see if the contract has been compiled
    assert os.path.exists(compiled_contract)

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")

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
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(contract_root, template, contract_name, None)

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

# Unfinished
def test_keys():
    """Test key command"""

    key = "sample_key"
    subprocess.run("fetchd keys add " + key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    # Requires password:
    # assert type(key_address) == type(subprocess.getoutput('jenesis alpha keys show ' + key))
