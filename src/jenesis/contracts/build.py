import fnmatch
import os
from typing import List, Optional, Any

from docker import from_env
from docker.errors import DockerException
from docker.types import Mount

from jenesis.contracts import Contract
from jenesis.tasks import Task, TaskStatus
from jenesis.tasks.monitor import run_tasks
from jenesis.config import Config

DEFAULT_BUILD_STEPS = [
    "RUSTFLAGS='-C link-arg=-s' cargo build --release --target wasm32-unknown-unknown",
    "mkdir -p artifacts",
    "mv target/wasm32-unknown-unknown/release/*.wasm artifacts/",
]

class ContractBuildTask(Task):

    BUILD_CONTAINER = 'cosmwasm/rust-optimizer:0.12.5'

    def __init__(self, contract: Contract, optimize: bool, rebuild: bool):
        self.contract = contract
        self._optimize = optimize
        self._rebuild = rebuild
        self._container = None
        self._status = TaskStatus.IDLE
        self._status_text = ''

    @property
    def name(self) -> str:
        return self.contract.name

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def status(self) -> TaskStatus:
        return self._status

    def poll(self):
        # no further processing required if it has either completed or failed
        if self.is_done:
            return

        # if the contract is not out of date then no build is required
        if self._container is None and not self._is_out_of_date() and not self._rebuild:
            self._status = TaskStatus.COMPLETE
            self._status_text = ''
            return

        # if we get this far we either need to schedule a docker build of the contract or we need to monitor
        # the progress of a docker build
        if self._container is None:
            cfg = Config.load(os.getcwd())
            try:
                self._container = self._schedule_build_container(self.contract, self._optimize)
                self._status = TaskStatus.IN_PROGRESS
                self._status_text = 'Building...'
                for profile in cfg.profiles.keys():
                    # pylint: disable=all
                    network_name = cfg.profiles[profile].network.name
                    Config.update_project(os.getcwd(), profile, network_name, self.contract)
            except DockerException:
                print("Error: looks like your docker setup isn't right, please visit https://jenesis.fetch.ai/ for more information")
                self._container = None
                self._status = TaskStatus.FAILED
                self._status_text = ''

            # exit if we do not have docker or some such installed
            if self._container is None:
                return

        assert self._container is not None

        # check on the progress of the container
        self._container.reload()

        if self._container.status == 'exited':
            exit_code = int(self._container.attrs['State']['ExitCode'])
            if exit_code == 0:
                self._status = TaskStatus.COMPLETE
                self._status_text = ''

                # clean up the container if it was successful, otherwise keep if for the logs
                self._container.remove()

            else:
                self._status = TaskStatus.FAILED
                self._status_text = ''

    def _is_out_of_date(self) -> bool:
        # determine the timestamp of the compiled contract
        if os.path.isfile(self.contract.binary_path):
            compiled_contract_timestamp = os.path.getmtime(self.contract.binary_path)
        else:
            compiled_contract_timestamp = 0

        # determine the timestamp of the contract source
        contract_source_timestamp = self._get_contract_modified_timestamp(self.contract.source_path)

        return contract_source_timestamp > compiled_contract_timestamp

    @classmethod
    def _schedule_build_container(cls, contract: Contract, optimize: bool):
        mounts = [
            Mount('/code/target', f'contract_{contract.name}_cache'),
            Mount('/usr/local/cargo/registry', 'registry_cache'),
            Mount('/code', os.path.abspath(contract.source_path), type='bind'),
        ]

        # get the docker client
        client = from_env()

        # start the container
        entrypoint = None if optimize else "/bin/sh"
        args = None if optimize else ["-c", " && ".join(DEFAULT_BUILD_STEPS)]
        return client.containers.run(cls.BUILD_CONTAINER, args, mounts=mounts, entrypoint=entrypoint, detach=True)

    @staticmethod
    def _get_src_files(path: str):
        for root, _, files in os.walk(path):
            for filename in fnmatch.filter(files, '*.rs'):
                yield os.path.join(root, filename)

    @classmethod
    def _get_contract_modified_timestamp(cls, path: str) -> float:
        src_path = os.path.join(path, 'src')
        return max(
            map(
                os.path.getmtime,
                cls._get_src_files(src_path)
            ),
            default=0
        )


def _chunks(values: List[Any], batch_size: Optional[int]):
    if batch_size is None:
        yield values
    else:
        for i in range(0, len(values), batch_size):
            yield values[i:i + batch_size]


def build_contracts(
    contracts: List[Contract],
    batch_size: Optional[int] = None,
    optimize: Optional[bool] = False,
    rebuild: Optional[bool] = False,
):
    """
    Will attempt to build all the specified contracts (provided they are out of date)

    :param contracts: The list of contracts to build
    :param batch_size: The max number of builds to do in parallel. If None then will attempt to all in parallel
    :param optimize: Whether to perform an optimized build
    :param rebuild: Whether to force a rebuild of the contracts
    :return:
    """
    # create all the tasks to be done
    tasks = list(
        map(
            ContractBuildTask,
            contracts,
            [optimize] * len(contracts),
            [rebuild] * len(contracts),
        )
    )

    # run the tasks (in batches if configured)
    for batch in _chunks(tasks, batch_size=batch_size):
        run_tasks(batch)


class WorkspaceBuildTask(Task):

    BUILD_CONTAINER = 'cosmwasm/workspace-optimizer:0.12.5'

    def __init__(self, path: str, contracts: List[Contract], optimize: bool, rebuild: bool):
        self._path = path
        self._contracts = contracts
        self._optimize = optimize
        self._rebuild = rebuild
        self._container = None
        self._status = TaskStatus.IDLE
        self._status_text = ''

    @property
    def name(self) -> str:
        return os.path.basename(self._path)

    @property
    def path(self) -> str:
        return self._path

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def status(self) -> TaskStatus:
        return self._status

    def poll(self):
        # no further processing required if it has either completed or failed
        if self.is_done:
            return

        # if the contract is not out of date then no build is required
        if self._container is None and not self._is_out_of_date() and not self._rebuild:
            self._status = TaskStatus.COMPLETE
            self._status_text = ''
            return

        # if we get this far we either need to schedule a docker build of the workspace or we need to monitor
        # the progress of a docker build
        if self._container is None:
            cfg = Config.load(os.getcwd())
            try:
                self._container = self._schedule_build_container(self._path, self._optimize)
                self._status = TaskStatus.IN_PROGRESS
                self._status_text = 'Building...'

                for profile in cfg.profiles.keys():
                    # pylint: disable=all
                    network_name = cfg.profiles[profile].network.name
                    for contract in self._contracts:
                        Config.update_project(os.getcwd(), profile, network_name, contract)
                        
            except DockerException:
                self._container = None
                self._status = TaskStatus.FAILED
                self._status_text = ''

            # exit if we do not have docker or some such installed
            if self._container is None:
                return

        assert self._container is not None

        # check on the progress of the container
        self._container.reload()

        if self._container.status == 'exited':
            exit_code = int(self._container.attrs['State']['ExitCode'])
            if exit_code == 0:
                self._status = TaskStatus.COMPLETE
                self._status_text = ''

                # clean up the container if it was successful, otherwise keep if for the logs
                self._container.remove()

            else:
                self._status = TaskStatus.FAILED
                self._status_text = ''

    def _is_out_of_date(self) -> bool:
        # determine the most recent timestamp of the compiled workspace files
        workspace_build_timestamp = self._get_workspace_build_timestamp(self._path)

        # determine the timestamp of the contract source
        contract_source_timestamp = self._get_contract_modified_timestamp(self._contracts)

        return contract_source_timestamp > workspace_build_timestamp

    @classmethod
    def _schedule_build_container(cls, path: str, optimize: bool):
        mounts = [
            Mount('/code/target', f'workspace_{os.path.basename(path)}_cache'),
            Mount('/usr/local/cargo/registry', 'registry_cache'),
            Mount('/code', os.path.abspath(path), type='bind'),
        ]

        # get the docker client
        client = from_env()

        # start the container
        entrypoint = None if optimize else "/bin/sh"
        args = None if optimize else ["-c", " && ".join(DEFAULT_BUILD_STEPS)]
        return client.containers.run(cls.BUILD_CONTAINER, args, mounts=mounts, entrypoint=entrypoint, detach=True)

    @staticmethod
    def _get_src_files(contracts: List[Contract]):
        for contract in contracts:
            src_path = os.path.join(contract.source_path, 'src')
            for root, _, files in os.walk(src_path):
                for filename in fnmatch.filter(files, '*.rs'):
                    yield os.path.join(root, filename)

    @staticmethod
    def _get_build_files(path: str):
        for root, _, files in os.walk(path):
            for filename in fnmatch.filter(files, '*.wasm'):
                yield os.path.join(root, filename)

    @classmethod
    def _get_contract_modified_timestamp(cls, contracts: List[Contract]) -> float:
        return max(
            map(
                os.path.getmtime,
                cls._get_src_files(contracts)
            ),
            default=0
        )

    @classmethod
    def _get_workspace_build_timestamp(cls, path: str) -> float:
        build_path = os.path.join(path, 'artifacts')
        return max(
            map(
                os.path.getmtime,
                cls._get_build_files(build_path)
            ),
            default=0
        )


def build_workspace(
    path: str,
    contracts: List[Contract],
    optimize: Optional[bool] = False,
    rebuild: Optional[bool] = False
):
    """
    Will attempt to build the cargo workspace including all contracts

    :param optimize: Whether to perform an optimized build
    :param rebuild: Whether to force a rebuild of the workspace
    :return:
    """
    # create all the tasks to be done
    tasks = [WorkspaceBuildTask(path, contracts, optimize, rebuild)]

    # run the tasks
    run_tasks(tasks)
