import argparse
import os
import toml

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

    data = toml.load("jenesis.toml")

    cfg = Config.load(project_root)
    profiles = list(cfg.profiles.keys())

    for profile_name in profiles:
        profile = cfg.profiles[profile_name]
        profile_contracts = list(profile.deployments.keys())

        if args.contract in profile_contracts:
            contract_data = data["profile"][profile_name]["contracts"][args.contract].copy()
            data["profile"][profile_name]["contracts"][args.deployment] = contract_data
            data["profile"][profile_name]["contracts"][args.deployment]["name"] = args.deployment

    project_configuration_file = os.path.join(project_root, "jenesis.toml")

    with open(project_configuration_file, "w", encoding="utf-8") as toml_file:
        toml.dump(data, toml_file)


def add_deployment_command(parser):
    deployment_cmd = parser.add_parser("deployment")
    deployment_cmd.add_argument("contract", help="The name of the contract to duplicate")
    deployment_cmd.add_argument("deployment", help="The name to assign the new deployment")
    deployment_cmd.set_defaults(handler=run)
