import argparse
import os
import toml

from jenesis.config import Config


def run(args: argparse.Namespace):

    project_root = os.path.abspath(os.getcwd())
    contract_root = os.path.join(project_root, "contracts", args.contract)

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_root, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return

    # check if the contract exists
    if not os.path.exists(contract_root):
        print(f'Contract "{args.contract}" doesnt exist')
        return

    data = toml.load("jenesis.toml")

    cfg = Config.load(project_root)
    profiles = list(cfg.profiles.keys())

    for profile in profiles:
        contract_data = data["profile"][profile]["contracts"][args.contract].copy()
        data["profile"][profile]["contracts"][args.deployment] = contract_data
        data["profile"][profile]["contracts"][args.deployment]["name"] = args.deployment
    
    project_configuration_file = os.path.join(project_root, "jenesis.toml")

    with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)


def add_deployment_command(parser):
    deployment_cmd = parser.add_parser("deployment")
    deployment_cmd.add_argument("contract", help="The name of the contract to duplicate")
    deployment_cmd.add_argument("deployment", help="The name to assign the new deployment")
    deployment_cmd.set_defaults(handler=run)
