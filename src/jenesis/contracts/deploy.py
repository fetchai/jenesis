import graphlib as gl
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ConcurrentTimeoutError
from typing import Dict, List, Optional, Set, Union

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.wallet import LocalWallet, Wallet
from cosmpy.crypto.address import Address
from cosmpy.crypto.keypairs import PrivateKey
from jenesis.config import Config, Deployment, Profile
from jenesis.contracts import Contract
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.keyring import (LocalInfo, query_keychain_item,
                             query_keychain_items)
from jenesis.network import run_local_node
from jenesis.tasks import Task, TaskStatus
from jenesis.tasks.monitor import run_tasks


# Recursive function to insert deployed contract address into instantiation msg
def insert(data: Union[Dict, List], contract_name: str, address: str):
    for key, value in data.items() if isinstance(data, dict) else enumerate(data):
        if value == contract_name:
            data[key] = address
        elif isinstance(value, (dict, list)):
            insert(value, contract_name, address)


def insert_address(contract_address_names: List[str], deployment: Deployment, profile: Profile) -> dict:

    deployment_names = list(profile.deployments.keys())

    # iterate over the addresses to insert
    for name in contract_address_names:
        if name in deployment_names:
            init_data = deployment.init
            deployed_contract_address = profile.deployments[name].address

            assert deployed_contract_address is not None, f"Contract {name} address not found"

            # insert deployed contract address in instantiation msg
            insert(init_data, name, str(deployed_contract_address))

    return init_data


def load_keys(key_names: Set[str]) -> Dict[str, PrivateKey]:
    keys = {}
    available_key_names = set(query_keychain_items())
    for key_name in key_names:

        if key_name not in available_key_names:
            print(f"Key not found: {key_name}")
            continue

        info = query_keychain_item(key_name)
        if not isinstance(info, LocalInfo):
            print(f"Failed to retrieve local key: {key_name}")
            continue

        keys[key_name] = PrivateKey(info.private_key)
    return keys


class DeployContractTask(Task):
    def __init__(self, project_path: str, cfg: Config, profile: Profile, contract: Contract,
                 deployment: Deployment, client: LedgerClient, wallet: Wallet):
        self._project_path = project_path
        self._cfg = cfg
        self._profile = profile
        self._contract = contract
        self._deployment = deployment
        self._client = client
        self._wallet = wallet

        # task status
        self._status = TaskStatus.IDLE
        self._status_text = ''

        # background worker
        self._executor = ThreadPoolExecutor(max_workers=1)

        # state machine state
        self._state = 'idle'
        self.ledger_contract = None  # type: Optional[LedgerContract]
        self.contract_address = None  # type: Optional[Address]
        self._future = None

    @property
    def name(self) -> str:
        return self._deployment.name

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def status_text(self) -> str:
        return self._status_text

    def poll(self):
        if self._state == 'idle':
            self._schedule_build_contract()
        elif self._state == 'wait-for-ledger-contract':
            self._wait_for_ledger_contract()
        elif self._state == 'schedule-deployment':
            self._schedule_deploy_contract()
        elif self._state == 'wait-for-deployment':
            self._wait_for_contract_deployment()
        elif self._state == 'failed':
            self._failed()
        elif self._state == 'complete':
            self._complete()
        else:
            assert False, "bad state"

    def _schedule_build_contract(self):
        assert self._future is None

        def action():
            return MonkeyContract(
                self._contract,
                self._client,
                code_id=self._deployment.code_id,
                address=self._deployment.address
            )

        self._future = self._executor.submit(action)
        self._state = 'wait-for-ledger-contract'
        self._status = TaskStatus.IN_PROGRESS
        self._status_text = '(1/2) Determining contract parameters...'

    def _wait_for_ledger_contract(self):
        try:
            self.ledger_contract = self._future.result(timeout=0.05)
            self._state = 'schedule-deployment'
            self._future = None
        except ConcurrentTimeoutError:
            pass

    def _schedule_deploy_contract(self):
        assert self._future is None
        assert self.ledger_contract is not None

        def action():
            return self.ledger_contract.deploy(
                args=self._deployment.init,
                sender=self._wallet,
                admin_address=self._wallet.address(),
                funds=self._deployment.init_funds,
            )

        self._future = self._executor.submit(action)
        self._state = 'wait-for-deployment'
        self._status = TaskStatus.IN_PROGRESS
        self._status_text = '(2/2) Deploying contract...'

    def _wait_for_contract_deployment(self):
        try:
            self.contract_address = self._future.result(timeout=0.05)
            self._state = 'complete'
            self._future = None
        except ConcurrentTimeoutError:
            pass

    def _complete(self):
        # update the configuration and save it to disk
        self._cfg.update_deployment(self._profile.name, self._deployment.name,
                                    self.ledger_contract.digest.hex(),
                                    self.ledger_contract.code_id, self.contract_address)
        self._cfg.save(self._project_path)

        self._finished(True)

    def _failed(self):
        self._finished(False)

    def _finished(self, success: bool):
        self._executor.shutdown(wait=True)
        if success:
            self._status = TaskStatus.COMPLETE
        else:
            self._status = TaskStatus.FAILED
        self._status_text = ''


def deploy_contracts(cfg: Config, project_path: str, deployer_key: Optional[str], profile_name: Optional[str] = None):
    if profile_name is None:
        profile_name = cfg.get_default_profile()

    profile = cfg.profiles[profile_name]

    if profile.network.is_local:
        run_local_node(profile.network)

    project_contracts = {contract.name: contract for contract in detect_contracts(project_path)}
    deployments = profile.deployments

    init_addresses = {
        name: set(deployment.init_addresses)
        for (name, deployment) in deployments.items()
    }

    # load all the keys required for this operation
    key_names = {deployment.deployer_key for deployment in deployments.values()} | {deployer_key}
    keys = load_keys(key_names)

    sorter = gl.TopologicalSorter(init_addresses)
    deployment_order = list(sorter.static_order())

    for deployment_name in deployment_order:
        deployment = deployments[deployment_name]

        # ensure specified contract is in project
        if deployment.contract not in project_contracts:
            print(f"Contract {deployment_name} not found in project")
            continue
        contract = project_contracts[deployment.contract]

        # ensure that contract has been compiled first
        if not os.path.isfile(contract.binary_path):
            print(f"No contract binary found for {contract.name}. Please run 'jenesis compile' first.")
            continue

        if deployer_key is not None:

            if deployer_key not in keys:
                print(f"Skipping {deployment_name}: deployer key {deployer_key} not available")
                continue

            deployment.deployer_key = deployer_key
            Config.update_key(os.getcwd(), profile_name, deployment_name, deployer_key)

        if deployment.address is not None:
            if not deployment.is_configuration_out_of_date():
                print(f"Skipping {deployment_name}: configuration is up to date")
                continue

            if contract.digest() == deployment.digest:
                print(f"Skipping {deployment_name}: digest has not changed")
                continue

        client = LedgerClient(profile.network)

        deployment.address = None  # clear the old address

        contract_address_names = init_addresses[deployment_name]

        if len(contract_address_names) > 0:
            deployment.init = insert_address(contract_address_names, deployment, profile)

        # lookup the wallet key
        wallet = LocalWallet(keys[deployment.deployer_key])

        # create the deployment task
        task = DeployContractTask(
            project_path,
            cfg,
            profile,
            contract,
            deployment,
            client,
            wallet,
        )

        # run the deployment task
        run_tasks([task])
