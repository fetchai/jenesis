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
    contract_name = "contract"

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", contract_name)

    Config.add_contract(project_root, template, contract_name, None)

    subprocess.run("jenesis run tests/jenesis/cmd/scripts/script.py", shell=True)

    os.remove("jenesis.toml")
    shutil.rmtree("contracts")