import hashlib
import json
import os
import shutil
import struct
import subprocess
from dataclasses import dataclass
from tempfile import mkdtemp
from typing import Any, Dict, List, Optional

import toml
from cosmpy.crypto.address import Address
from jenesis.config.errors import ConfigurationError
from jenesis.config.extract import (extract_opt_dict, extract_opt_int,
                                    extract_opt_str, extract_req_dict,
                                    extract_req_str, extract_req_str_list,
                                    extract_opt_list)
from jenesis.contracts import Contract
from jenesis.contracts.detect import detect_contracts, parse_contract
from jenesis.network import (Network, fetchai_localnode_config,
                             fetchai_testnet_config, fetchai_mainnet_config)


TEMPLATE_GIT_URL = "https://github.com/fetchai/jenesis-templates.git"
DEFAULT_KEYRING_BACKEND = "os"


@dataclass
class Deployment:
    name: str # internal: the name for the deployment
    contract: str  # internal: the name of the contract to deploy
    network: str  # internal: the name of the network to deploy to
    deployer_key: str  # config: the name of the key to use for deployment
    init: Any  # config: init parameters for the contract
    init_funds: Optional[str] # config: funds to be sent with instantiation msg
    checksum: Optional[str]  # lock: the checksum digest to detect configuration changes
    digest: Optional[str]  # lock: the contract of the deployed contract
    address: Optional[Address]  # lock: the address of the deployed contract
    code_id: Optional[int]  # lock: the code of the deployed contract

    def reset_metadata(self):
        self.checksum = None
        self.digest = None
        self.address = None
        self.code_id = None

    def compute_checksum(self) -> str:
        hasher = hashlib.sha256()

        def update(value: Optional[Any]):
            encoded_value = "" if value is None else str(value)

            hasher.update(struct.pack(">Q", len(encoded_value)))
            hasher.update(encoded_value.encode())

        canonical_init_args = json.dumps(self.init, sort_keys=True)

        update(self.network)
        update(self.deployer_key)
        update(canonical_init_args)
        update(self.digest)
        update(self.address)
        update(self.code_id)

        return hasher.hexdigest()

    def __repr__(self) -> str:
        return f'{self.contract}: {self.address}'

    def is_configuration_out_of_date(self) -> bool:
        return self.checksum != self.compute_checksum()

    def to_lockfile(self) -> Any:
        data = {
            "checksum": self.compute_checksum(),
        }

        if self.digest is not None:
            data["digest"] = str(self.digest)
        if self.address is not None:
            data["address"] = str(self.address)
        if self.code_id is not None:
            data["code_id"] = self.code_id

        return data


@dataclass
class Profile:
    name: str
    network: Network
    deployments: Dict[str, Deployment]
    default: bool = False

    def to_lockfile(self) -> Any:
        return {
            name: deployment.to_lockfile()
            for name, deployment in self.deployments.items()
        }


@dataclass
class Config:
    project_name: str
    project_authors: List[str]
    profiles: Dict[str, Profile]
    keyring_backend: str = "os"

    def update_deployment(
        self,
        profile_name: str,
        deployment_name: str,
        digest: str,
        code_id: int,
        address: Address,
    ):
        profile = self.profiles.get(profile_name)
        if profile is None:
            raise ConfigurationError(f"unable to lookup profile {profile_name}")

        deployment = profile.deployments.get(deployment_name)
        assert deployment is not None, f"Deployment not found: {deployment_name}"

        # update the contract if necessary
        if digest is not None:
            deployment.digest = str(digest)
        if code_id is not None:
            deployment.code_id = int(code_id)
        if address is not None:
            deployment.address = Address(address)

        profile.deployments[deployment_name] = deployment
        self.profiles[profile_name] = profile

    def get_default_profile(self) -> str:
        for (name, profile) in self.profiles.items():
            if profile.default:
                return name
        return self.profiles.keys()[0]

    def get_profile(self, profile_name: Optional[str]) -> Optional[Profile]:
        if profile_name is None:
            profile_name = self.get_default_profile()
        else:
            if profile_name not in self.profiles:
                print(f'Invalid profile name. Expected one of {",".join(self.profiles.keys())}')
                return None
        return self.profiles[profile_name]

    @classmethod
    def load(cls, path: str) -> "Config":
        project_file_path = os.path.join(path, "jenesis.toml")
        lock_file_path = os.path.join(path, "jenesis.lock")

        if not os.path.isfile(project_file_path):
            raise ConfigurationError('Missing project file: "jenesis.toml"')
        project_contents = toml.load(project_file_path)

        if os.path.isfile(lock_file_path):
            lock_file_contents = toml.load(lock_file_path)
        else:
            lock_file_contents = {}

        return cls._loads(project_contents, lock_file_contents)

    @classmethod
    def _loads(cls, project_contents: Any, lock_file_contents: Any) -> "Config":

        # extract the profiles section
        config_profiles = project_contents.get("profile", {})
        if not isinstance(config_profiles, dict):
            raise ConfigurationError("invalid profile configuration section")

        lock_profiles = lock_file_contents.get("profile", {})
        if not isinstance(lock_profiles, dict):
            raise ConfigurationError("invalid profile lock section")

        profiles = {}
        for name, config_item in config_profiles.items():
            lock_item = lock_profiles.get(name, {})

            profile = cls._parse_profile(name, config_item, lock_item)
            profiles[profile.name] = profile

        keyring_backend = extract_opt_str(
            project_contents, "project.keyring_backend"
        ) or DEFAULT_KEYRING_BACKEND

        return Config(
            project_name=extract_req_str(project_contents, "project.name"),
            project_authors=extract_req_str_list(project_contents, "project.authors"),
            profiles=profiles,
            keyring_backend=keyring_backend,
        )

    @classmethod
    def _parse_profile(cls, name: str, profile: Any, lock_profile: Any) -> Profile:
        if not isinstance(profile, dict):
            raise ConfigurationError(
                "profile configuration invalid, expected dictionary"
            )
        if not isinstance(lock_profile, dict):
            raise ConfigurationError(
                "profile lock configuration invalid, expected dictionary"
            )

        network = Network(**extract_req_dict(profile, "network"))

        profile_contracts = profile.get("contracts", {})
        if not isinstance(profile_contracts, dict):
            raise ConfigurationError("invalid contracts section in config")

        deployments = {}
        if "contracts" in profile:
            for deployment_name, contract_cfg in profile_contracts.items():
                deployment_lock = lock_profile.get(deployment_name, {})

                deployment = cls._parse_contract_config(
                    deployment_name, contract_cfg, network.name, deployment_lock
                )
                deployments[deployment_name] = deployment

        is_default = False
        if "default" in profile:
            if profile["default"]:
                is_default = True

        return Profile(
            name=str(name),
            network=network,
            deployments=deployments,
            default=is_default,
        )

    @classmethod
    def _parse_contract_config(
        cls, deployment_name: str, contract_cfg: dict, network: str, lock: Any
    ) -> Deployment:
        if not isinstance(contract_cfg, dict):
            raise ConfigurationError(
                "contract configuration invalid, expected dictionary"
            )
        if not isinstance(lock, dict):
            raise ConfigurationError(
                "contract lock configuration invalid, expected dictionary"
            )

        def opt_address(value: Optional[str]) -> Optional[Address]:
            return None if value is None else Address(value)

        return Deployment(
            name=str(deployment_name),
            contract=extract_req_str(contract_cfg, "contract"),
            network=str(network),
            init=extract_opt_dict(contract_cfg, "init"),
            deployer_key=extract_req_str(contract_cfg, "deployer_key"),
            init_funds=extract_opt_str(contract_cfg, "init_funds"),
            digest=extract_opt_str(lock, "digest"),
            address=opt_address(extract_opt_str(lock, "address")),
            code_id=extract_opt_int(lock, "code_id"),
            checksum=extract_opt_str(lock, "checksum"),
        )

    def save(self, path: str):
        contents = {
            "profile": {
                name: profile.to_lockfile() for name, profile in self.profiles.items()
            }
        }

        lock_file_path = os.path.join(path, "jenesis.lock")
        with open(lock_file_path, "w", encoding="utf-8") as lock_file:
            toml.dump(contents, lock_file)

    @staticmethod
    def create_project(path: str, profile: str, network_name: str):
        user_name = subprocess.getoutput("git config user.name")
        user_email = subprocess.getoutput("git config user.email")
        authors = [f"{user_name} <{user_email}>"]

        # take the project name directly from the base name of the project
        project_root = os.path.abspath(path)
        project_name = os.path.basename(project_root)

        # detect contract source code and add placeholders for key contract data
        contracts = detect_contracts(project_root) or []

        deployments = {contract.name: Deployment(contract.name, contract.name,
            network_name, "", {arg: "" for arg in contract.init_args()},
            "", None, None, None, None,
        ) for contract in contracts}

        if network_name == "fetchai-testnet":
            net_config = fetchai_testnet_config()
        elif network_name == "fetchai-localnode":
            net_config = fetchai_localnode_config()
        elif network_name == "fetchai-mainnet":
            net_config = fetchai_mainnet_config()
        else:
            raise ConfigurationError("Network name not recognized")

        network = {"name": network_name}
        network.update(vars(net_config))

        profiles = {
            profile: {
                "network": network,
                "contracts": {name: vars(cfg) for (name, cfg) in deployments.items()},
                "default": True,
            }
        }

        data = {
            "project": {"name": project_name, "authors": authors, "keyring_backend": "os"},
            "profile": profiles,
        }

        project_configuration_file = os.path.join(project_root, "jenesis.toml")
        project_git_keep_files = [
            os.path.join(project_root, "contracts", ".gitkeep"),
        ]

        # create the configuration file
        os.makedirs(os.path.dirname(project_configuration_file), exist_ok=True)
        with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
            toml.dump(data, toml_file)

        # create all the git kep files
        for git_keep_path in project_git_keep_files:
            os.makedirs(os.path.dirname(git_keep_path), exist_ok=True)

            with open(git_keep_path, "a", encoding="utf-8"):
                pass

    @staticmethod
    def update_project(path: str, profile: str, network_name: str, contract: Contract):

        # take the project name directly from the base name of the project
        project_root = os.path.abspath(path)

        # set deployment name to contract name by default
        deployment_name = contract.name

        deployment = Deployment(deployment_name, contract.name,
            network_name, "", {arg: "" for arg in contract.init_args()},
            "", None, None, None, None)

        data = toml.load("jenesis.toml")

        data["profile"][profile]["contracts"][contract.name] = vars(deployment)
        project_configuration_file = os.path.join(project_root, "jenesis.toml")

        with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
            toml.dump(data, toml_file)

    @staticmethod
    def update_key(path: str, profile: str, deployment_name: str, key: str):

        # take the project name directly from the base name of the project
        project_root = os.path.abspath(path)

        input_file_name = "jenesis.toml"
        path = os.path.join(os.getcwd(), input_file_name)
        with open(path, encoding="utf-8") as toml_file:
            data = toml.load(toml_file)

        data["profile"][profile]["contracts"][deployment_name]["deployer_key"] = key
        project_configuration_file = os.path.join(project_root, "jenesis.toml")

        with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
            toml.dump(data, toml_file)

    @staticmethod
    def add_profile(path: str, profile: str, network_name: str):

        data = toml.load("jenesis.toml")

        if network_name == "fetchai-testnet":
            net_config = fetchai_testnet_config()
        elif network_name == "fetchai-localnode":
            net_config = fetchai_localnode_config()
        elif network_name == "fetchai-mainnet":
            net_config = fetchai_mainnet_config()
        else:
            raise ConfigurationError("Network name not recognized")

        network = {"name": ""}
        network.update(vars(net_config))

        # detect contract source code and add placeholders for key contract data
        contracts = detect_contracts(path) or []

        contract_cfgs = {
            contract.name: Deployment(
                contract.name,
                contract.name,
                network_name,
                "",
                {arg: "" for arg in contract.init_args()},
                "",
                None,
                None,
                None,
                None,
            )
            for contract in contracts
        }

        data["profile"][profile] = {
            "network": network,
            "contracts": {name: vars(cfg) for (name, cfg) in contract_cfgs.items()},
        }

        output_file_name = "jenesis.toml"
        with open(output_file_name, "w") as toml_file:
            # pylint: disable=all
            toml.dump(data, toml_file)

    @staticmethod
    def add_contract(project_root: str, template: str, name: str, branch: str) -> Contract:

        contract_path = os.path.join(project_root, 'contracts', name)

        # create the temporary clone folder
        temp_clone_path = mkdtemp(prefix="jenesis-", suffix="-tmpl")

        # clone the templates folder out in the temporary file
        print("Downloading template...")
        cmd = ["git", "clone", "--single-branch"]
        if branch is not None:
            cmd += ["--branch", branch]
        cmd += [TEMPLATE_GIT_URL, "."]
        with open(os.devnull, "w", encoding="utf8") as null_file:
            subprocess.check_call(
                cmd, stdout=null_file, stderr=subprocess.STDOUT, cwd=temp_clone_path
            )

        # find the target contract
        available_templates = os.listdir(os.path.join(temp_clone_path, "contracts"))
        contract_template_path = os.path.join(temp_clone_path, "contracts", template)
        if not os.path.isdir(contract_template_path):
            print(f"Unknown template {template}: expecting one of {set(available_templates)}")
            return
        print("Downloading template...complete")

        # process all the files as part of the template
        print("Rendering template...")
        for root, _, files in os.walk(contract_template_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, contract_template_path)

                output_filepath = os.path.join(contract_path, rel_path)
                os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
                with open(file_path, "r", encoding="utf8") as input_file:
                    with open(output_filepath, "w", encoding="utf8") as output_file:
                        contents = input_file.read()

                        # replace the templating parameters here
                        contents = contents.replace("<<NAME>>", name)

                        output_file.write(contents)
        print("Rendering template...complete")

        # clean up the temporary folder
        shutil.rmtree(temp_clone_path)

        return parse_contract(project_root, name)
