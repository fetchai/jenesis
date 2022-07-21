import hashlib
import json
import os
import struct
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import toml
from cosmpy.crypto.address import Address
from haul.config.errors import ConfigurationError
from haul.config.extract import (extract_opt_int, extract_opt_str,
                                 extract_req_dict, extract_req_str,
                                 extract_req_str_list)


@dataclass
class ContractConfig:
    name: str  # internal: the name of the contract
    network: str  # internal: the name of the network to deploy to
    deployer_key: str  # config: the name of the key to use for deployment
    init: Any  # config: init parameters for the contract
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
    network: str
    contracts: Dict[str, ContractConfig]

    def to_lockfile(self) -> Any:
        return {
            name: contract.to_lockfile() for name, contract in self.contracts.items()
        }


@dataclass
class Config:
    project_name: str
    project_authors: List[str]
    profiles: Dict[str, Profile]

    def update_deployment(
        self,
        profile_name: str,
        contract_name: str,
        digest: str,
        code_id: int,
        address: Address,
    ):
        profile = self.profiles.get(profile_name)
        if profile is None:
            raise ConfigurationError(f"unable to lookup profile {profile_name}")

        contract = profile.contracts.get(contract_name)
        if contract is None:
            raise ConfigurationError(f"unable to lookup contract {contract_name}")

        # update the contract
        contract.digest = str(digest)
        contract.code_id = int(code_id)
        contract.address = Address(address)

        profile.contracts[contract_name] = contract
        self.profiles[profile_name] = profile

    @classmethod
    def load(cls, path: str) -> "Config":
        project_file_path = os.path.join(path, "haul.toml")
        lock_file_path = os.path.join(path, "haul.lock")

        project_contents = toml.load(project_file_path)
        lock_file_contents = toml.load(lock_file_path)

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

        return Config(
            project_name=extract_req_str(project_contents, "project.name"),
            project_authors=extract_req_str_list(project_contents, "project.authors"),
            profiles=profiles,
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

        network = extract_req_str(profile, "network")

        profile_contracts = profile.get("contracts", {})
        if not isinstance(profile_contracts, dict):
            raise ConfigurationError("invalid contracts section in config")

        contracts = {}
        if "contracts" in profile:
            for contract_name, contract_settings in profile_contracts.items():
                contract_lock = lock_profile.get(contract_name, {})

                contract = cls._parse_contract_config(
                    network, contract_name, contract_settings, contract_lock
                )
                contracts[contract.name] = contract

        return Profile(
            name=str(name),
            network=network,
            contracts=contracts,
        )

    @classmethod
    def _parse_contract_config(
        cls, network: str, name: str, details: Any, lock: Any
    ) -> ContractConfig:
        if not isinstance(details, dict):
            raise ConfigurationError(
                "contract configuration invalid, expected dictionary"
            )
        if not isinstance(lock, dict):
            raise ConfigurationError(
                "contract lock configuration invalid, expected dictionary"
            )

        def opt_address(value: Optional[str]) -> Optional[Address]:
            return None if value is None else Address(value)

        return ContractConfig(
            name=str(name),
            network=str(network),
            init=extract_req_dict(details, "init"),
            deployer_key=extract_req_str(details, "deployer_key"),
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

        lock_file_path = os.path.join(path, "haul.lock")
        with open(lock_file_path, "w", encoding="utf-8") as lock_file:
            toml.dump(contents, lock_file)

    @staticmethod
    def create_project(path: str):
        user_name = subprocess.getoutput("git config user.name")
        user_email = subprocess.getoutput("git config user.email")
        authors = [f"{user_name} <{user_email}>"]

        # take the project name directly from the base name of the project
        project_root = os.path.abspath(path)
        project_name = os.path.basename(project_root)

        data = {
            "project": {"name": project_name, "authors": authors},
            "profile": {
                "testing": {
                    "network": "fetchai-dorado",
                }
            },
        }

        project_configuration_file = os.path.join(project_root, "haul.toml")
        project_git_keep_files = [
            os.path.join(project_root, "contracts", ".gitkeep"),
        ]

        # check to see if the project file already exists
        if os.path.exists(project_configuration_file):
            print("Project already initialized")
            sys.exit(1)

        try:

            # create the configuration file
            os.makedirs(os.path.dirname(project_configuration_file), exist_ok=True)
            with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
                toml.dump(data, toml_file)

            # create all the git kep files
            for git_keep_path in project_git_keep_files:
                os.makedirs(os.path.dirname(git_keep_path), exist_ok=True)

                with open(git_keep_path, "a", encoding="utf-8"):
                    pass

        except FileExistsError:
            print("Project already initialized")
