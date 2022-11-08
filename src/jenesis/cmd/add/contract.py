import argparse
import os

from jenesis.config import Config


def add_contract_command(parser):

    add_contract_cmd = parser.add_parser("contract")
    add_contract_cmd.add_argument("template", help="The name of the template to use")
    add_contract_cmd.add_argument("name", help="The name of contract to create")
    add_contract_cmd.add_argument('deployments', nargs='+', help='contract deployments')
    add_contract_cmd.add_argument(
        "-p",
        "--profile",
        default=None,
        help="Profile where the deployments will be added to",
    )
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

    cfg = Config.load(project_root)

    profile_name = args.profile or cfg.get_default_profile()
    selected_profile = cfg.profiles[profile_name]

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_root, "jenesis.toml")):
        print("Please run command from project root")
        return False

    # check to see if the contract already exists
    if os.path.exists(contract_root):
        print(f'Contract "{name}" already exists')
        return False

    selected_contract = Config.add_contract(project_root, template, name, branch)

    if selected_contract is None:
        return False

    network_name = selected_profile.network.name
    for deployment in args.deployments:
        Config.update_project(os.getcwd(), profile_name, network_name, selected_contract, deployment)

    return True
