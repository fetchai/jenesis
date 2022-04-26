import fnmatch
import os
from typing import List, Optional, Any

from docker import from_env
from docker.errors import DockerException
from docker.types import Mount

from haul.contracts import Contract
from haul.tasks import Task, TaskStatus
from haul.tasks.monitor import run_tasks


class ContractBuildTask(Task):

    BUILD_CONTAINER = 'cosmwasm/rust-optimizer:0.12.5'

    def __init__(self, contract: Contract):
        self.contract = contract
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
        if self._container is None and not self._is_out_of_date():
            self._status = TaskStatus.COMPLETE
            self._status_text = ''
            return

        # if we get this far we either need to schedule a docker build of the contract or we need to monitor
        # the progress of a docker build
        if self._container is None:
            try:
                self._container = self._schedule_build_container(self.contract)
                self._status = TaskStatus.IN_PROGRESS
                self._status_text = 'Building...'
            except DockerException:
                self._container = None
                self._status = TaskStatus.FAILED
                self._status_text = ''

            # exit if we do not have docker or some such installed
            if self._container is None:
                return

        assert self._container is not None

        # check on the progress of the co
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
    def _schedule_build_container(cls, contract: Contract):
        mounts = [
            Mount('/code/target', f'contract_{contract.name}_cache'),
            Mount('/usr/local/cargo/registry', 'registry_cache'),
            Mount('/code', os.path.abspath(contract.source_path), type='bind'),
        ]

        # get the docker client
        client = from_env()

        # start the container
        return client.containers.run(cls.BUILD_CONTAINER, mounts=mounts, detach=True)

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


def build_contracts(contracts: List[Contract], batch_size: Optional[int] = None):
    """
    Will attempt to build all the specified contracts (provided they are out of date)

    :param contracts: The list of contracts to build
    :param batch_size: The max number of builds to do in parallel. If None then will attempt to all in parallel
    :return:
    """
    # create all the tasks to be done
    tasks = list(
        map(
            ContractBuildTask,
            contracts,
        )
    )

    # run the tasks (in batches if configured)
    for batch in _chunks(tasks, batch_size=batch_size):
        run_tasks(batch)
