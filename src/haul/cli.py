import argparse
import sys
from typing import Tuple

from haul.cmd.compile import add_compile_command
from haul.cmd.deploy import add_deploy_command
from haul.cmd.init import add_init_command
from haul.cmd.keys import add_keys_command
from haul.cmd.new import add_new_command
from haul.cmd.shell import add_shell_command


def _parse_commandline() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    add_init_command(subparsers)
    add_new_command(subparsers)
    add_compile_command(subparsers)
    add_shell_command(subparsers)
    add_deploy_command(subparsers)
    add_keys_command(subparsers)

    return parser, parser.parse_args()


def main():
    parser, args = _parse_commandline()

    exit_code = 1
    if hasattr(args, 'handler'):
        result = args.handler(args)
        if isinstance(result, bool) and result:
            exit_code = 0
        elif isinstance(result, int):
            exit_code = result
        elif result is None:
            exit_code = 0

    else:
        parser.print_usage()

    if exit_code != 0:
        sys.exit(exit_code)
