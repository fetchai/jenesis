import argparse


def run(_args: argparse.Namespace):
    print('Implement me!')


def add_init_command(parser):
    init_cmd = parser.add_parser('init')
    init_cmd.set_defaults(handler=run)
