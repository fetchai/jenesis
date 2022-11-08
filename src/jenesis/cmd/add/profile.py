import argparse
import os

from jenesis.config import Config


def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return

    Config.add_profile(args.profile, args.network)



def add_profile_command(parser):
    profile_cmd = parser.add_parser("profile")
    profile_cmd.add_argument("profile", default="testing", help="The profile to create")
    profile_cmd.add_argument(
        "-n", "--network", default="fetchai-testnet", help="Network to use"
    )
    profile_cmd.set_defaults(handler=run)
