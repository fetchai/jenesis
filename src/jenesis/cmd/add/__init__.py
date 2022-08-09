import argparse

from jenesis.cmd.add.contract import run_add_contract


def add_add_command(parser):
    add_cmd = parser.add_parser('add')
    subparsers = add_cmd.add_subparsers()

    add_contract_cmd = subparsers.add_parser('contract', help='Contract service templates')
    add_contract_cmd.add_argument('template', help='The name of the template to use')
    add_contract_cmd.add_argument('name', help='The name of contract to create')
    add_contract_cmd.add_argument('-b', '--branch', help='The name of the branch that should be used')
    add_contract_cmd.set_defaults(handler=run_add_contract)
