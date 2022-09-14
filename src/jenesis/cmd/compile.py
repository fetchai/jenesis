import hashlib
import argparse
import os
import json
import struct

from blessings import Terminal
from jenesis.contracts.build import build_contracts, build_workspace
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts, is_workspace
from jenesis.contracts.schema import generate_schemas

def compute_init_schema(path, contract_name):

    file_name = "instantiate_msg.json"
    file_path = os.path.join(path, "contracts", contract_name,"schema", file_name)

    with open(file_path , 'r', encoding="utf-8") as file:
        data = json.load(file)

    hasher = hashlib.sha256()
    encoded_value = "" if data is None else str(data)

    hasher.update(struct.pack(">Q", len(encoded_value)))
    hasher.update(encoded_value.encode())
    print(hasher.hexdigest())
    return hasher.hexdigest()


def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        print("Please run command from project root")
        return 1

    term = Terminal()

    contracts = detect_contracts(project_path)
    if contracts is None or len(contracts) == 0:
        print(term.red("Unable to detect any contracts"))
        return 1

    init_checksums = {contract.name: compute_init_schema(project_path, contract.name) for contract in contracts}

    if is_workspace(project_path):
        print(term.green("\nBuilding cargo workspace..."))
        build_workspace(project_path, contracts, optimize=args.optimize, rebuild=args.rebuild)
    else:
        print(term.green("\nBuilding contracts..."))
        build_contracts(contracts, batch_size=args.batch_size, optimize=args.optimize,rebuild=args.rebuild)

    # generate the schemas
    print(term.green("\nGenerating contract schemas..."))
    generate_schemas(contracts, batch_size=args.batch_size, rebuild=args.rebuild)

    cfg = Config.load(os.getcwd())
    for contract in contracts:
        if compute_init_schema(project_path, contract.name) != init_checksums[contract.name]:
            print("ding ding")
            # update project file
            for (profile_name, profile) in cfg.profiles.items():
                network_name = profile.network.name
                Config.update_project(project_path, profile_name, network_name, contract)

    return 0


def add_compile_command(parser):
    compile_cmd = parser.add_parser("compile")
    compile_cmd.add_argument(
        "-p",
        dest="batch_size",
        type=int,
        help="The limit of the number of tasks to do in parallel",
    )
    compile_cmd.add_argument(
        "-o",
        "--optimize",
        action = "store_true",
        help="Optimize build",
    )
    compile_cmd.add_argument(
        "-r",
        "--rebuild",
        action = "store_true",
        help="Force rebuild",
    )
    compile_cmd.set_defaults(handler=run)
