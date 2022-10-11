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

    network = "fetchai-localnode"
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

    subprocess.run("jenesis deploy " + deployment_key, shell=True)

    file_path = os.path.dirname(os.path.realpath(__file__))

    script_path = os.path.join(file_path, "scripts/script.py")

    output = subprocess.run(
        "jenesis run " + script_path, shell=True,stdout=subprocess.PIPE)

    output_string = output.stdout.decode()

    start = 'jenesis run output:'
    end = '\nShutting'

    result = output_string[output_string.find(start)+len(start):output_string.find(end)]

    assert result == "{'count': 8}"

    # shutil.rmtree(path)