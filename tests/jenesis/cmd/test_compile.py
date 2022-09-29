import os
import shutil
import subprocess
import time
from tempfile import mkdtemp

import pytest
from jenesis.config import Config


#@pytest.mark.skip
def test_compile_contract():
    """Test compile contract"""

    network = "fetchai-testnet"
    profile = "profile_1"

    path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    Config.create_project(path, profile, network)

    template = "starter"
    contract_name = "contract"

    project_root = os.path.abspath(path)
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(project_root, template, contract_name, None)

    os.chdir(path)
    subprocess.run("jenesis compile -l", shell=True)
    time.sleep(60)

    compiled_contract = os.path.join(
        contract_root, "artifacts", contract_name + ".wasm"
    )

    # check to see if the contract has been compiled
    assert os.path.exists(compiled_contract)

    #os.remove("jenesis.toml")
    #shutil.rmtree("contracts")


    # clean up the temporary folder

    # <<<<<<<<<<<<<<
    #shutil.rmtree(path)
    # <<<<<<<<<<<<<<