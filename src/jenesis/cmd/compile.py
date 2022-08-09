import argparse
import os

from blessings import Terminal

from jenesis.contracts.build import build_contracts, build_workspace
from jenesis.contracts.detect import detect_contracts, is_workspace


def run(args: argparse.Namespace):
    term = Terminal()

    contracts = detect_contracts(os.getcwd())
    if contracts is None or len(contracts) == 0:
        print(term.red('Unable to detect any contracts'))
        return 1

    if is_workspace(os.getcwd()):
        build_workspace(os.getcwd(), contracts)
        return 0

    # build the contracts
    build_contracts(contracts, batch_size=args.batch_size)
    return 0


def add_compile_command(parser):
    compile_cmd = parser.add_parser('compile')
    compile_cmd.add_argument('-p', dest='batch_size', type=int, help='The limit of the number of tasks to do in parallel')
    compile_cmd.set_defaults(handler=run)
