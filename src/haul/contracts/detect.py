import os
from typing import List, Optional

import toml

from haul.contracts import Contract


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
            'Cargo.lock',
        )
        for expected_file in expected_files:
            if not os.path.isfile(os.path.join(contract_path, expected_file)):
                return False

        return True

    def parse_contract(name: str) -> Contract:
        cargo_file_path = os.path.join(contracts_folder, name, 'Cargo.toml')
        with open(cargo_file_path, 'r', encoding="utf-8") as cargo_file:
            cargo_contents = toml.load(cargo_file)

        # extract the contract name
        contract_name = cargo_contents['package']['name']

        return Contract(
            name=name,
            source_path=os.path.abspath(os.path.join(contracts_folder, name)),
            binary_path=os.path.abspath(os.path.join(contracts_folder, name, 'artifacts', f'{contract_name}.wasm'))
        )

    contracts = map(
        parse_contract,
        filter(
            is_contract,
            os.listdir(contracts_folder)
        )
    )

    return list(contracts)
