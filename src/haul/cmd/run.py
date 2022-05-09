import argparse
import os

from cosmpy.aerial.client import LedgerClient
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.aerial.wallet import LocalWallet

from haul.config import Config
from haul.contracts.detect import detect_contracts
from haul.contracts.monkey import MonkeyContract
from haul.contracts.networks import get_network_config
from haul.contracts.observer import ContractConfigUpdator


def run(args: argparse.Namespace):
    project_path = os.getcwd()

    # determine the
    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    # need a ledger client

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
            selected_contract = selected_profile.contracts.get(contract.name)
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
                observer=ContractConfigUpdator(
                    cfg,
                    project_path,
                    args.profile,
                    contract.name,
                )
            )

            contract_instances[contract.name] = monkey

    print('Detecting contracts...complete')

    shell_globals = {}
    shell_globals['cfg'] = cfg
    shell_globals['project_path'] = project_path
    shell_globals['profile'] = args.profile
    shell_globals['contracts'] = contract_instances

    exec(open(args.script_path).read(), shell_globals)


def add_run_command(parser):
    run_cmd = parser.add_parser('run')
    run_cmd.add_argument('-p', '--profile', default='testing', help='The profile to use')
    run_cmd.add_argument('script_path', help='The path to the script to run')
    run_cmd.set_defaults(handler=run)
