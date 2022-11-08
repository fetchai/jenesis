import os
import shutil
from tempfile import mkdtemp

import toml
from jenesis.config import Config


def test_add_profile():
    """Test adding new profiles"""

    networks = ["fetchai-testnet", "fetchai-localnode"]
    chain_ids = ["dorado-1", "localnode"]
    profiles = ["profile_1", "profile_2", "profile_3", "profile_4"]

    temp_clone_path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

    os.chdir(temp_clone_path)

    path = os.getcwd()

    Config.create_project(path, profiles[0], networks[1])

    for (i, profile) in enumerate(profiles[1:]):
        Config.add_profile(profile, networks[i % 2])

    input_file_name = "jenesis.toml"
    toml_path = os.path.join(path, input_file_name)
    with open(toml_path, encoding="utf-8") as toml_file:
        data = toml.load(toml_file)

    profile_list = list(data["profile"].keys())

    for (i, profile) in enumerate(profiles):
        assert profile_list[i] == profile
        assert data["profile"][profile]["network"]["name"] == networks[(i + 1) % 2]
        assert data["profile"][profile]["network"]["chain_id"] == chain_ids[(i + 1) % 2]

    # clean up the temporary folder
    #shutil.rmtree(temp_clone_path)