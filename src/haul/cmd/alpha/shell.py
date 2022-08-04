import argparse

from ptpython import embed


def run(_args: argparse.Namespace):
    embed(globals(), locals(), vi_mode=False)


def add_shell_command(parser):
    shell_cmd = parser.add_parser('shell')
    shell_cmd.set_defaults(handler=run)
