import os
import shutil
import subprocess
from tempfile import mkdtemp
from jenesis.cmd import compile
from jenesis.config import Config


class Arguments:
    batch_size = 1
    optimize = ""
    rebuild = ""
    log = ""


def test_attach():
    """Test attach contract"""

    # create project
    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    os.chdir(path)

    template = "starter"
    contract_name = "contract"
    deployment_name = "deployment"

    project_root = os.path.abspath(os.getcwd())

    # use deployed contract address
    contract_address = "fetch1xf6hdf4k9luwapstgmhxfn8lhlzn4hq056daprkx9x2fw4r2tyfqc8qrtq"

    Config.create_project("project_1", profile, network)
    os.chdir(os.path.join(path, "project_1"))

    contract_root = os.path.join(project_root,"project_1", "contracts", contract_name)

    project_root = os.path.abspath(os.getcwd())

    # add contract and update
    contract = Config.add_contract(project_root, template, contract_name, None)
    Config.update_project(os.getcwd(), profile, network, contract, deployment_name)

    # compile contract
    args = Arguments()
    compile.run(args)

    compiled_contract = os.path.join(
        contract_root, "artifacts", contract_name + ".wasm"
    )

    # check if the contract has been compiled
    assert os.path.exists(compiled_contract)

    # attach previously deployed contract
    subprocess.run(
        "jenesis attach " + deployment_name + " " + contract_address, shell=True
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
