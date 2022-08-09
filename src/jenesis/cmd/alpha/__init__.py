import argparse

from jenesis.cmd.alpha.deploy import add_deploy_command
from jenesis.cmd.alpha.keys import add_keys_command
from jenesis.cmd.alpha.run import add_run_command
from jenesis.cmd.alpha.shell import add_shell_command


def add_alpha_command(parser):
    alpha_cmd = parser.add_parser('alpha')
    subparsers = alpha_cmd.add_subparsers()

    add_deploy_command(subparsers)
    add_keys_command(subparsers)
    add_run_command(subparsers)
    add_shell_command(subparsers)
