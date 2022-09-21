import os
from typing import List, Optional

import toml

from jenesis.contracts import Contract
from jenesis.contracts.schema import load_contract_schema


def is_workspace(path: str) -> bool:
    contracts_folder = os.path.join(path, 'contracts')
    if not os.path.isdir(contracts_folder):
        return False

    expected_files = (
        'Cargo.toml',
        'Cargo.lock',
    )
    for expected_file in expected_files:
        if not os.path.isfile(os.path.join(path, expected_file)):
            return False

    return True


def detect_contracts(path: str) -> Optional[List[Contract]]:
    contracts_folder = os.path.join(path, 'contracts')
    if not os.path.isdir(contracts_folder):
        return None

    def is_contract(folder_name: str) -> bool:
        contract_path = os.path.join(contracts_folder, folder_name)
        if not os.path.isdir(contract_path):
            return False

        expected_files = (
            'Cargo.toml',
        )
        for expected_file in expected_files:
            if not os.path.isfile(os.path.join(contract_path, expected_file)):
                return False

        return True

    def parse_contract(name: str) -> Contract:
        cargo_file_path = os.path.join(contracts_folder, name, 'Cargo.toml')
        with open(cargo_file_path, 'r', encoding="utf-8") as cargo_file:
            cargo_contents = toml.load(cargo_file)

        # extract the contract name and replace hyphens with underscores
        contract_name = cargo_contents['package']['name'].replace("-", "_")

        source_path = os.path.abspath(os.path.join(contracts_folder, name))
        if is_workspace(path):
            cargo_root = path
        else:
            cargo_root = os.path.join(contracts_folder, name)
        artifacts_path = os.path.join(cargo_root, 'artifacts')
        binary_path = os.path.abspath(os.path.join(artifacts_path, f'{contract_name}.wasm'))

        schema = load_contract_schema(source_path)

        return Contract(
            name=name,
            source_path=source_path,
            binary_path=binary_path,
            cargo_root=cargo_root,
            schema=schema,
        )

    contracts = map(
        parse_contract,
        filter(
            is_contract,
            os.listdir(contracts_folder)
        )
    )

    return list(contracts)
