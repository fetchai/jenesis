import argparse
import os

from cosmpy.aerial.client import LedgerClient
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.contracts.networks import get_network_config
import toml

def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return

    cfg = Config.load(project_path)

    if args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        return

    selected_profile = cfg.profiles[args.profile]
    network_cfg = get_network_config(selected_profile.network)
    if network_cfg is None:
        print("No network configuration for this profile")
        return

    contracts = detect_contracts(project_path)

    selected_contract = ""
    for contract in contracts:
        if contract.name == args.contract:
            selected_contract = contract
            continue

    if selected_contract == "":
        print('Contract not found in project')
        return

    client = LedgerClient(network_cfg)

    contract = MonkeyContract(selected_contract.binary_path, client, args.address)
    code_id = contract.code_id
    digest = contract.digest.hex()

    data = toml.load("jenesis.toml") 

    network = data["profile"][args.profile]["network"]

    Config.update_project(project_path, args.profile, network, selected_contract)
    cfg.update_deployment(
        selected_profile.name, args.contract, digest, code_id, args.address
    )
    cfg.save(project_path)


def add_attach_command(parser):
    attach_cmd = parser.add_parser("attach")
    attach_cmd.add_argument("contract", help="Contract name")
    attach_cmd.add_argument("address", help="Contract address")
    attach_cmd.add_argument(
        "-p",
        "--profile",
        default="testing",
        help="Profile where the contract will be attached",
    )
    attach_cmd.set_defaults(handler=run)