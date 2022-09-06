from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError
from typing import Optional, Tuple, List

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.wallet import LocalWallet, Wallet
from cosmpy.crypto.address import Address
from cosmpy.crypto.keypairs import PrivateKey

from jenesis.config import Config, Deployment, Profile
from jenesis.contracts import Contract
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.keyring import query_keychain_item, LocalInfo, query_keychain_items
from jenesis.network import run_local_node
from jenesis.tasks import Task, TaskStatus
from jenesis.tasks.monitor import run_tasks
import os


class DeployContractTask(Task):
    def __init__(self, project_path: str, cfg: Config, profile: Profile, contract: Contract, config: Deployment,
                 client: LedgerClient, wallet: Wallet):
        self._project_path = project_path
        self._cfg = cfg
        self._profile = profile
        self._contract = contract
        self._config = config
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
        return self._contract.name

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def status_text(self) -> str:
        return self._status_text

    def poll(self):
        # print('POLL', self._state, self._status, self._status_text, self.name)

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
                code_id=self._config.code_id,
                address=self._config.address
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
                args=self._config.init,
                sender=self._wallet,
                admin_address=self._wallet.address()
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
        self._cfg.update_deployment(self._profile.name, self._contract.name,
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


def deploy_contracts(cfg: Config, project_path: str, deployer_key: Optional[str], profile: Optional[str] = None):
    # pylint: disable=all
    if profile is None:
        profile = cfg.get_default_profile()

    selected_profile = cfg.profiles[profile]

    if selected_profile.network.is_local:
        run_local_node(selected_profile.network)

    contracts = detect_contracts(project_path)

    contracts_to_deploy = []  # type: List[Tuple[Contract, Deployment]]
    profile_contracts = selected_profile.contracts
    profile_contract_names = list(profile_contracts.keys())

    # determine what tasks to do
    for contract in contracts:
        if contract.name in profile_contract_names:
            profile_contract = selected_profile.deployments.get(contract.name)
        else:
            continue
        assert profile_contract is not None

        if deployer_key is not None:
            profile_contract.deployer_key = deployer_key
            Config.update_key(os.getcwd(), profile, contract, deployer_key)

        # simple case the contract is already deployed and we can just use the information directly from the lockfile
        if profile_contract.is_configuration_out_of_date():
            contracts_to_deploy.append((contract, profile_contract))
            continue

        digest = contract.digest()
        if digest is None:
            continue  # we can't process any contracts where we don't have

        assert digest is not None

        # if the digest of the contract has changed then we need to add it to the list of contracts to deploy
        if profile_contract.digest != digest:
            contracts_to_deploy.append((contract, profile_contract))
            continue

    # exit if there is nothing to do
    if len(contracts_to_deploy) == 0:
        print('Nothing to deploy')
        return

    client = LedgerClient(selected_profile.network)

    # load all the keys required for this operation
    keys = {}
    available_key_names = set(query_keychain_items())
    all_keys = set(settings.deployer_key for _, settings in contracts_to_deploy)

    for key_name in all_keys:
        if key_name not in available_key_names:
            print(f'Unknown deployment key {key_name}')
            return

        info = query_keychain_item(key_name)
        if not isinstance(info, LocalInfo):
            print(f'Unable to lookup local key {key_name}')
            return

        keys[key_name] = PrivateKey(info.private_key)

    for contract, _ in contracts_to_deploy:
        # reset this contracts metadata
        contract_settings = selected_profile.deployments[contract.name]
        contract_settings.address = None  # clear the old address

        # lookup the wallet key
        wallet = LocalWallet(keys[contract_settings.deployer_key])

        # create the deployment task
        task = DeployContractTask(
            project_path,
            cfg,
            selected_profile,
            contract,
            contract_settings,
            client,
            wallet,
        )

        # run the deployment task
        run_tasks([task])

    return
