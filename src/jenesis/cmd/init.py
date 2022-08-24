import argparse
import os

from jenesis.config import Config


def run(args: argparse.Namespace):

    project_path = os.getcwd()
    Config.create_project(project_path, args.profile)


def add_init_command(parser):
    init_cmd = parser.add_parser("init")
    init_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to initialize"
    )
    init_cmd.set_defaults(handler=run)
