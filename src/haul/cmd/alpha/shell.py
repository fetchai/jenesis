import argparse
import os

from ptpython import embed

from cosmpy.aerial.client import LedgerClient

from haul.config import Config
from haul.contracts.detect import detect_contracts
from haul.contracts.monkey import MonkeyContract
from haul.contracts.networks import get_network_config
from haul.contracts.observer import DeploymentUpdater


def load_config(args: argparse.Namespace) -> dict:
    project_path = os.getcwd()

    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    print('Detecting contracts...')

    contract_instances = {}
    selected_profile = cfg.profiles.get(args.profile)
    if selected_profile is not None:
        net_config = get_network_config(selected_profile.network)
        if net_config is None:
            raise RuntimeError(f'Unknown network name "{selected_profile.network}"')

        # build the ledger client
        client = LedgerClient(net_config)

        for contract in contracts:
            print('C', contract)

            # skip contracts that we have not compiled
            if contract.digest() is None:
                continue

            # select the metadata for the contract
            selected_contract = selected_profile.deployments.get(contract.name)
            if selected_contract is not None:
                address = selected_contract.address
                code_id = selected_contract.code_id
            else:
                code_id = None
                address = None

            monkey = MonkeyContract(
                contract.binary_path,
                client,
                address=address,
                code_id=code_id,
                observer=DeploymentUpdater(
                    cfg,
                    project_path,
                    args.profile,
                    contract.name,
                ),
                init_args=selected_contract.init,
            )

            contract_instances[contract.name] = monkey

    print('Detecting contracts...complete')

    shell_globals = {}
    shell_globals['cfg'] = cfg
    shell_globals['project_path'] = project_path
    shell_globals['profile'] = args.profile
    shell_globals['contracts'] = {contract.name: contract for contract in contracts}
    for (name, instance) in contract_instances.items():
        shell_globals[name] = instance

    return shell_globals


def run(args: argparse.Namespace):

    shell_globals = load_config(args)
    shell_globals.update(globals())
    embed(shell_globals, vi_mode=False, history_filename='.shell_history')


def add_shell_command(parser):
    shell_cmd = parser.add_parser('shell')
    shell_cmd.add_argument('-p', '--profile', default='testing', help='The profile to use')
    shell_cmd.set_defaults(handler=run)
