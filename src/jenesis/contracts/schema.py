import os

from typing import List, Optional

from jenesis.contracts import Contract
from jenesis.contracts.build import ContractBuildTask
from jenesis.tasks.utils import chunks
from jenesis.tasks.monitor import run_tasks

SCHEMA_BUILD_STEPS = ["cargo schema"]


class ContractSchemaTask(ContractBuildTask):

    def __init__(self, contract: Contract, rebuild: bool):
        super().__init__(contract, False, rebuild)
        self._build_steps = SCHEMA_BUILD_STEPS
        self._working_dir = os.path.join('/code', 'contracts', os.path.basename(contract.source_path))
        self._in_progress_text = "Generating schemas..."


def generate_schemas(
    contracts: List[Contract],
    batch_size: Optional[int] = None,
    rebuild: Optional[bool] = False,
):
    """
    Will attempt to build all the specified contract schemas (provided they are out of date)

    :param contracts: The list of contracts to build schemas for
    :param batch_size: The max number of builds to do in parallel. If None then will attempt to all in parallel
    :param rebuild: Whether to force a rebuild of the contract schemas
    :return:
    """
    # create all the tasks to be done
    tasks = list(
        map(
            ContractSchemaTask,
            contracts,
            [rebuild] * len(contracts),
        )
    )

    # run the tasks (in batches if configured)
    for batch in chunks(tasks, batch_size=batch_size):
        run_tasks(batch)
