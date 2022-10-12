import os
import shutil
import subprocess
import time
from tempfile import mkdtemp

import pytest
import toml
from jenesis.config import Config


#@pytest.mark.skip
def test_deploy_run_contract():
    """Test deploy contract and run cmd"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")
    os.chdir(path)

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())

    contract = Config.add_contract(project_root, template, contract_name, None)

    Config.update_project(os.getcwd(), profile, network, contract)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    file_path = os.path.dirname(os.path.realpath(__file__))

    script_path = os.path.join(file_path, "scripts/deploy_contract.py")

    output = subprocess.run(
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    output_string = output.stdout.decode()

    start = 'jenesis run output:'

    result = output_string[output_string.find(start)+len(start):].replace("\n", "")

    assert result == "{'count': 8}"

    #shutil.rmtree(path)