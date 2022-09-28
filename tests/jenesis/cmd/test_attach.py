import os
import shutil
import subprocess
import time

import pytest
from jenesis.config import Config


@pytest.mark.skip
def test_attach_contract():
    """Test attach contract"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = os.getcwd()

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "C"

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(project_root, template, contract_name, None)

    subprocess.run("jenesis compile", shell=True)
    time.sleep(60)

    compiled_contract = os.path.join(
        contract_root, "artifacts", contract_name + ".wasm"
    )

    # check to see if the contract has been compiled
    assert os.path.exists(compiled_contract)

    subprocess.run("jenesis attach C fetch10jasvh4m80jm3t65vhmlf0awwgrfnt47x0e430gyp4unak77wkwsev7jvw", shell=True)

    time.sleep(15)

    subprocess.run("jenesis run tests/jenesis/cmd/scripts/script.py", shell=True)

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")