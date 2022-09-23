import argparse
import os

from cosmpy.aerial.client import LedgerClient
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.network import Network
import toml

def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return 1

    cfg = Config.load(project_path)

    if args.profile is not None and args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        return 1

    profile_name = args.profile or cfg.get_default_profile()

    selected_profile = cfg.profiles[profile_name]

    if args.contract not in selected_profile.deployments:
        print('Deployment not found in project')
        return 1
    deployment = selected_profile.deployments[args.contract]

    client = LedgerClient(selected_profile.network)

    project_contracts = {contract.name: contract for contract in detect_contracts(project_path)}

    contract = MonkeyContract(project_contracts[deployment.contract], client, args.address)
    code_id = contract.code_id
    digest = contract.digest.hex()

    data = toml.load("jenesis.toml") 

    network = Network(**data["profile"][profile_name]["network"])

    Config.update_project(project_path, profile_name, network.name, project_contracts[deployment.contract])

    cfg.update_deployment(
        selected_profile.name, deployment.name, digest, code_id, args.address
    )
    cfg.save(project_path)
    return 0


def add_attach_command(parser):
    attach_cmd = parser.add_parser("attach")
    attach_cmd.add_argument("contract", help="Contract name")
    attach_cmd.add_argument("address", help="Contract address")
    attach_cmd.add_argument(
        "-p",
        "--profile",
        default=None,
        help="Profile where the contract will be attached",
    )
    attach_cmd.set_defaults(handler=run)