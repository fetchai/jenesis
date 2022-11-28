import argparse
import os

from jenesis.contracts.detect import parse_contract
from jenesis.config import Config


def run(args: argparse.Namespace):

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", args.contract)

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_root, "jenesis.toml")):
        print("Please run command from project root")
        return

    # check if the contract exists
    if not os.path.exists(contract_root):
        print(f'Contract "{args.contract}" does not exist')
        return

    cfg = Config.load(project_root)

    profile_name = cfg.get_default_profile()

    selected_contract = parse_contract(project_root , args.contract)


    for (profile_name, profile) in cfg.profiles.items():
        network_name = profile.network.name
        for deployment in args.deployments:
            Config.update_project(os.getcwd(), profile_name, network_name, selected_contract, deployment)


def add_deployment_command(parser):
    deployment_cmd = parser.add_parser("deployment")
    deployment_cmd.add_argument("contract", help="The name of the contract that the deployment points to")
    deployment_cmd.add_argument('deployments', nargs='+', help='contract deployments',)
    deployment_cmd.set_defaults(handler=run)
