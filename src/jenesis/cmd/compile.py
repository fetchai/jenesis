import argparse
import os

from blessings import Terminal
from jenesis.contracts.build import build_contracts, build_workspace
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts, is_workspace
from jenesis.contracts.schema import generate_schemas


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

    if is_workspace(project_path):
        print(term.green("\nBuilding cargo workspace..."))
        build_workspace(project_path, contracts, optimize=args.optimize, rebuild=args.rebuild)
    else:
        print(term.green("\nBuilding contracts..."))
        build_contracts(contracts, batch_size=args.batch_size, optimize=args.optimize,rebuild=args.rebuild)

    # generate the schemas
    print(term.green("\nGenerating contract schemas..."))
    generate_schemas(contracts, batch_size=args.batch_size, rebuild=args.rebuild)

    # update project file
    cfg = Config.load(os.getcwd())
    for (profile_name, profile) in cfg.profiles.items():
        network_name = profile.network.name
        for contract in contracts:
            Config.update_project(os.getcwd(), profile_name, network_name, contract)

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
