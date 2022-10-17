import os
from typing import List, Optional

from docker import from_env
from docker.models.containers import Container
from docker.types import Mount

from jenesis.contracts import Contract
from jenesis.tasks.container import ContainerTask
from jenesis.tasks.monitor import run_tasks
from jenesis.tasks.utils import chunks, get_last_modified_timestamp

DEFAULT_BUILD_STEPS = [
    "RUSTFLAGS='-C link-arg=-s' cargo build --release --lib --target wasm32-unknown-unknown",
    "mkdir -p artifacts",
    "mv target/wasm32-unknown-unknown/release/*.wasm artifacts/",
]


class ContractBuildTask(ContainerTask):

    BUILD_CONTAINER = 'cosmwasm/rust-optimizer:0.12.9'

    def __init__(self, contract: Contract, optimize: bool, rebuild: bool, log: bool):
        super().__init__()
        self.contract = contract
        self._optimize = optimize
        self._rebuild = rebuild
        self._log = log
        self._build_steps = DEFAULT_BUILD_STEPS
        self._working_dir = '/code'
        self._in_progress_text = 'Building...'

    @property
    def name(self) -> str:
        return self.contract.name

    def _is_out_of_date(self) -> bool:
        #  pylint: disable=duplicate-code
        if self._rebuild:
            return True

        # determine the timestamp of the compiled contract
        if os.path.isfile(self.contract.binary_path):
            compiled_contract_timestamp = os.path.getmtime(self.contract.binary_path)
        else:
            compiled_contract_timestamp = 0

        # determine the timestamp of the contract source
        src_path = os.path.join(self.contract.source_path, 'src')
        contract_source_timestamp = get_last_modified_timestamp([src_path], 'rs')

        return contract_source_timestamp > compiled_contract_timestamp

    def _schedule_container(self) -> Container:
        mounts = [
            Mount('/code/target', f'contract_{self.contract.name}_cache'),
            Mount('/usr/local/cargo/registry', 'registry_cache'),
            Mount('/code', os.path.abspath(self.contract.cargo_root), type='bind'),
        ]

        # get the docker client
        client = from_env()

        # start the container
        entrypoint = None if self._optimize else "/bin/sh"
        args = None if self._optimize else ["-c", " && ".join(self._build_steps)]
        return client.containers.run(
            self.BUILD_CONTAINER,
            args,
            mounts=mounts,
            working_dir=self._working_dir,
            entrypoint=entrypoint,
            detach=True,
        )

    def _show_logs(self):
        return self._log


def build_contracts(
    contracts: List[Contract],
    batch_size: Optional[int] = None,
    optimize: Optional[bool] = False,
    rebuild: Optional[bool] = False,
    log: Optional[bool] = False,
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
            [log] * len(contracts),
        )
    )

    # run the tasks (in batches if configured)
    for batch in chunks(tasks, batch_size=batch_size):
        run_tasks(batch)


class WorkspaceBuildTask(ContainerTask):

    BUILD_CONTAINER = 'cosmwasm/workspace-optimizer:0.12.9'

    def __init__(self, path: str, contracts: List[Contract], optimize: bool, rebuild: bool, log: bool):
        super().__init__()
        self._path = path
        self._contracts = contracts
        self._optimize = optimize
        self._rebuild = rebuild
        self._log = log

    @property
    def name(self) -> str:
        return os.path.basename(self._path)

    @property
    def path(self) -> str:
        return self._path

    def _is_out_of_date(self) -> bool:
        if self._rebuild:
            return True

        # determine the most recent timestamp of the compiled workspace files
        build_path = os.path.join(self._path, 'artifacts')
        workspace_build_timestamp = get_last_modified_timestamp([build_path], 'wasm')

        # determine the timestamp of the contract source
        contract_src_paths = [f'{contract.source_path}/src' for contract in self._contracts]
        contract_source_timestamp = get_last_modified_timestamp(contract_src_paths, 'rs')

        return contract_source_timestamp > workspace_build_timestamp

    def _schedule_container(self) -> Container:
        mounts = [
            Mount('/code/target', f'workspace_{os.path.basename(self.path)}_cache'),
            Mount('/usr/local/cargo/registry', 'registry_cache'),
            Mount('/code', os.path.abspath(self.path), type='bind'),
        ]

        # get the docker client
        client = from_env()

        # start the container
        entrypoint = None if self._optimize else "/bin/sh"
        args = None if self._optimize else ["-c", " && ".join(DEFAULT_BUILD_STEPS)]
        return client.containers.run(
            self.BUILD_CONTAINER,
            args,
            mounts=mounts,
            entrypoint=entrypoint,
            detach=True,
        )

    def _show_logs(self):
        return self._log

def build_workspace(
    path: str,
    contracts: List[Contract],
    optimize: Optional[bool] = False,
    rebuild: Optional[bool] = False,
    log: Optional[bool] = False
):
    """
    Will attempt to build the cargo workspace including all contracts

    :param optimize: Whether to perform an optimized build
    :param rebuild: Whether to force a rebuild of the workspace
    :return:
    """
    # create all the tasks to be done
    tasks = [WorkspaceBuildTask(path, contracts, optimize, rebuild, log)]

    # run the tasks
    run_tasks(tasks)
