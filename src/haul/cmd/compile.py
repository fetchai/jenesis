import argparse
import os

from blessings import Terminal

from haul.contracts.build import build_contracts
from haul.contracts.detect import detect_contracts


def run(args: argparse.Namespace):
    term = Terminal()

    contracts = detect_contracts(os.getcwd())
    if contracts is None:
        print(term.red('Unable to detect any contracts'))
        return 1

    # build the contracts
    build_contracts(contracts, batch_size=args.batch_size)
    return 0


def add_compile_command(parser):
    compile_cmd = parser.add_parser('compile')
    compile_cmd.add_argument('-p', dest='batch_size', type=int, help='The limit of the number of tasks to do in parallel')
    compile_cmd.set_defaults(handler=run)
