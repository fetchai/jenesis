import argparse
import os

from jenesis.config import Config
from jenesis.contracts.deploy import deploy_contracts


def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return 1

    cfg = Config.load(project_path)

    if args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        return 1

    deploy_contracts(cfg, project_path, args.key, profile=args.profile)
    return 0


def add_deploy_command(parser):
    deploy_cmd = parser.add_parser("deploy")
    deploy_cmd.add_argument(
        "-p", "--profile", default=None, help="The profile to deploy"
    )
    deploy_cmd.add_argument("key", nargs="?", help="Deployer Key for all contracts")
    deploy_cmd.set_defaults(handler=run)
