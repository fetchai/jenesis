import os
import shutil
import subprocess
from tempfile import mkdtemp

import toml
from jenesis.config import Config
from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi
from jenesis.cmd import compile


class Arguments:
    batch_size = 1
    optimize = ""
    rebuild = ""
    log = ""


def test_deploy_run_contract():
    """Test deploy contract and run cmd"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")
    os.chdir(path)

    # create project
    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", contract_name)

    # add starter contract and update
    contract = Config.add_contract(project_root, template, contract_name, None)
    Config.update_project(os.getcwd(), profile, network, contract)

    # compile contract
    args = Arguments()
    compile.run(args)

    compiled_contract = os.path.join(
        contract_root, "artifacts", contract_name + ".wasm"
    )

    # check if the contract has been compiled
    assert os.path.exists(compiled_contract)

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

    # set fetchd to test keyring backend
    subprocess.run("fetchd config keyring-backend test", shell=True)

    # add key
    deployment_key = "test_key"
    subprocess.run("fetchd keys add " + deployment_key, shell=True)

    # add atestfet funds to key
    key_address = subprocess.getoutput("fetchd keys show -a " + deployment_key)
    faucet = FaucetApi(NetworkConfig.fetchai_stable_testnet())
    faucet.get_wealth(str(key_address))

    # deploy using key
    subprocess.run('jenesis deploy ' + deployment_key, shell = True)

    file_path = os.path.dirname(os.path.realpath(__file__))
    script_path = os.path.join(file_path, "scripts/query_contract.py")

    # run script
    output = subprocess.run(
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    # get script output
    output_string = output.stdout.decode()
    start = 'jenesis run output:'
    result = output_string[output_string.find(start)+len(start):].replace("\n", "")

    assert result == "{'count': 5}"

    #shutil.rmtree(path)