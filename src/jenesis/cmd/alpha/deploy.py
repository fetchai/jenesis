import argparse
import os

from jenesis.config import Config
from jenesis.contracts.deploy import deploy_contracts


def run(args: argparse.Namespace):
    cfg = Config.load(os.getcwd())

    if args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        return 1

    deploy_contracts(cfg, args.profile, os.getcwd(), args.key)
    return 0


def add_deploy_command(parser):
    deploy_cmd = parser.add_parser("deploy")
    deploy_cmd.add_argument(
        "-p", "--profile", default="testing", help="The profile to deploy"
    )
    deploy_cmd.add_argument("key", nargs='?', metavar="KEY", help="Deployer Key for all contracts")
    deploy_cmd.set_defaults(handler=run)
