import hashlib
import argparse
import os
import struct

from blessings import Terminal
from jenesis.contracts.build import build_contracts, build_workspace
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts, is_workspace
from jenesis.contracts.schema import generate_schemas, load_contract_schema


def _compute_init_checksum(path, contract_name):
    schema_path = os.path.join(path, "contracts", contract_name)
    schema = load_contract_schema(schema_path)

    # check for workspace-style schema
    if contract_name in schema:
        schema = schema[contract_name]

    hasher = hashlib.sha256()
    encoded_value = "" if schema is None else str(schema)

    hasher.update(struct.pack(">Q", len(encoded_value)))
    hasher.update(encoded_value.encode())
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

    init_checksums = {contract.name: _compute_init_checksum(project_path, contract.name) for contract in contracts}

    if is_workspace(project_path):
        print(term.green("\nBuilding cargo workspace..."))
        build_workspace(project_path, contracts, optimize=args.optimize, rebuild=args.rebuild, log=args.log)
    else:
        print(term.green("\nBuilding contracts..."))
        build_contracts(contracts, batch_size=args.batch_size, optimize=args.optimize,rebuild=args.rebuild, log=args.log)

    # generate the schemas
    print(term.green("\nGenerating contract schemas..."))
    generate_schemas(contracts, batch_size=args.batch_size, rebuild=args.rebuild)

    contracts = detect_contracts(project_path)

    cfg = Config.load(os.getcwd())
    for contract in contracts:
        if _compute_init_checksum(project_path, contract.name) != init_checksums[contract.name]:
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
        default=5,
        help="The limit of the number of tasks to do in parallel (default = 5)",
    )
    compile_cmd.add_argument(
        "-o",
        "--optimize",
        action="store_true",
        help="Optimize build",
    )
    compile_cmd.add_argument(
        "-r",
        "--rebuild",
        action="store_true",
        help="Force rebuild",
    )
    compile_cmd.add_argument(
        "--log",
        action="store_true",
        help="Show build logs (default)",
    )
    compile_cmd.add_argument(
        "--no-log",
        dest="log",
        action="store_false",
        help="Do not show build logs",
    )
    compile_cmd.set_defaults(handler=run, log=True)
