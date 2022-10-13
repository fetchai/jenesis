import argparse

from jenesis.cmd.add.contract import run_add_contract
from jenesis.cmd.add.contract import add_contract_command
from jenesis.cmd.add.profile import add_profile_command
from jenesis.cmd.add.deployment import add_deployment_command


def add_add_command(parser):

    add_cmd = parser.add_parser('add')
    subparsers = add_cmd.add_subparsers()

    add_contract_command(subparsers)
    add_profile_command(subparsers)
    add_deployment_command(subparsers)
