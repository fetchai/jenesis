import argparse
import os
import toml

from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts


def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return False

    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    contracts_to_update = []

    data = toml.load("jenesis.toml")

    profiles = list(cfg.profiles.keys())
    current_contracts = data["profile"][profiles[0]]["contracts"].keys()

    for contract in contracts:
        if not contract.name in current_contracts:
            contracts_to_update.append(contract)
            
    if len(contracts_to_update) == 0:
        print('Nothing to update')
        return
               
    for profile in profiles:
        for contract in contracts_to_update:
            network_name = cfg.profiles[profile].network.name
            Config.update_project(os.getcwd(), profile, network_name, contract)
    
    print("Contracts up to date!")


def add_update_command(parser):
    update_cmd = parser.add_parser("update")
    update_cmd.set_defaults(handler=run)