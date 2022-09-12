import argparse
import os

from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts


def add_contract_command(parser):

    add_contract_cmd = parser.add_parser("contract")
    add_contract_cmd.add_argument("template", help="The name of the template to use")
    add_contract_cmd.add_argument("name", help="The name of contract to create")
    add_contract_cmd.add_argument(
        "-b", "--branch", help="The name of the branch that should be used"
    )
    add_contract_cmd.set_defaults(handler=run_add_contract)


def run_add_contract(args: argparse.Namespace):
    template = args.template
    name = args.name
    branch = args.branch

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", name)

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_root, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return False

    # check to see if the contract already exists
    if os.path.exists(contract_root):
        print(f'Contract "{name}" already exists')
        return False

    Config.add_contract(contract_root, template, name, branch)

    contracts = detect_contracts(project_root)

    selected_contract = ""
    for contract in contracts:
        if contract.name == name:
            selected_contract = contract
            continue

    if selected_contract == "":
        print("Contract not found in project")
        return

    cfg = Config.load(project_root)

    for profile in cfg.profiles.keys():
        network_name = cfg.profiles[profile].network.name
        Config.update_project(os.getcwd(), profile, network_name, selected_contract)

    return True
