import argparse
import os

from ptpython import embed

from haul.config import Config
from haul.contracts.detect import detect_contracts
# from haul.contracts.monkey import MonkeyContract


# def _load_contract_info(project_path: str, profile: str) -> Dict[str, MonkeyContract]:
#     # load up the contract and configuration data for the project
#     return {}


def run(_args: argparse.Namespace):
    project_path = os.getcwd()

    # determine the
    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    shell_globals = globals()
    shell_globals['cfg'] = cfg
    shell_globals['project_path'] = project_path
    shell_globals['profile'] = _args.profile
    shell_globals['contracts'] = {contract.name: contract for contract in contracts}

    embed(globals(), vi_mode=False)


def add_shell_command(parser):
    shell_cmd = parser.add_parser('shell')
    shell_cmd.add_argument('-p', '--profile', default='testing', help='The profile to use')
    shell_cmd.set_defaults(handler=run)
