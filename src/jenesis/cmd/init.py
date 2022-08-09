import argparse
import os

from jenesis.config import Config


def run(_args: argparse.Namespace):
    Config.create_project(os.getcwd())


def add_init_command(parser):
    init_cmd = parser.add_parser("init")
    init_cmd.set_defaults(handler=run)
