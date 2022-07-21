import argparse
import os

from haul.config import Config


def run(_args: argparse.Namespace):

    project_name = os.path.basename(os.getcwd())
    Config.create_project(project_name)


def add_init_command(parser):
    init_cmd = parser.add_parser("init")
    init_cmd.set_defaults(handler=run)
