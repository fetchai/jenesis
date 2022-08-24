import argparse
import os

from jenesis.config import Config


def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check if the project has been already initialized
    if os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Project already initialized")
        return

    Config.create_project(project_path, args.profile, args.network)


def add_init_command(parser):
    init_cmd = parser.add_parser("init")
    init_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to initialize"
    )
    init_cmd.add_argument(
        "-n", "--network", default="fetchai-testnet", help="Network to use"
    )
    init_cmd.set_defaults(handler=run)