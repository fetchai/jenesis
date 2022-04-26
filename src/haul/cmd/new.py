import argparse


def run(_args: argparse.Namespace):
    print('Implement me!')


def add_new_command(parser):
    new_cmd = parser.add_parser('new')
    new_cmd.set_defaults(handler=run)
