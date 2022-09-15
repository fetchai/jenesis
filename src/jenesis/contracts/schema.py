import json
import os

from typing import List, Optional

from jenesis.contracts import Contract
from jenesis.contracts.build import ContractBuildTask
from jenesis.tasks.utils import chunks, get_last_modified_timestamp
from jenesis.tasks.monitor import run_tasks

SCHEMA_BUILD_STEPS = ["cargo schema"]


class ContractSchemaTask(ContractBuildTask):

    def __init__(self, contract: Contract, rebuild: bool):
        super().__init__(contract, False, rebuild)
        self._build_steps = SCHEMA_BUILD_STEPS
        self._working_dir = os.path.join('/code', 'contracts', os.path.basename(contract.source_path))
        self._in_progress_text = "Generating schemas..."

    def _is_out_of_date(self) -> bool:
        #  pylint: disable=duplicate-code
        if self._rebuild:
            return True

        # determine the timestamp of the compiled contract
        if os.path.isfile(self.contract.binary_path):
            compiled_contract_timestamp = os.path.getmtime(self.contract.binary_path)
        else:
            compiled_contract_timestamp = 0

        # determine the timestamp of the contract schema files
        schema_path = os.path.join(self.contract.source_path, 'schema')
        contract_schema_timestamp = get_last_modified_timestamp([schema_path], 'json')

        return compiled_contract_timestamp > contract_schema_timestamp


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

    for contract in contracts:
        contract.schema = load_contract_schema(contract.source_path)


def load_contract_schema(source_path: str) -> dict:
    schema_folder = os.path.join(source_path, 'schema')
    if not os.path.isdir(schema_folder):
        return None

    schema = {}
    for filename in os.listdir(schema_folder):
        if filename.endswith('.json'):
            msg_name = os.path.splitext(os.path.basename(filename))[0]
            full_path = os.path.join(schema_folder, filename)
            with open(full_path, 'r', encoding="utf-8") as msg_schema_file:
                msg_schema = json.load(msg_schema_file)
            schema[msg_name] = msg_schema
    return schema
