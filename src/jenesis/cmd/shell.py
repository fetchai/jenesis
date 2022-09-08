import argparse
import os

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from ptpython import embed
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.contracts.observer import DeploymentUpdater
from jenesis.keyring import query_keychain_items, query_keychain_item
from jenesis.network import run_local_node


def load_config(args: argparse.Namespace) -> dict:
    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        raise RuntimeError("Please run command from project root or create project first")

    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    shell_globals = {}
    contract_instances = {}

    if args.profile is not None and args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        return

    profile_name = args.profile or cfg.get_default_profile()

    selected_profile = cfg.profiles.get(profile_name)
    if selected_profile is not None:
        if selected_profile.network.is_local:
            run_local_node(selected_profile.network)

        # build the ledger client
        client = LedgerClient(selected_profile.network)

        print(f'Network: {selected_profile.network.name}')

        print('Detecting contracts...')

        for contract in contracts:
            print("C", contract)

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
                contract,
                client,
                address=address,
                code_id=code_id,
                observer=DeploymentUpdater(
                    cfg,
                    project_path,
                    profile_name,
                    contract.name,
                ),
                init_args=selected_contract.init,
            )

            contract_instances[contract.name] = monkey

        print('Detecting contracts...complete')
        
        shell_globals["ledger"] = LedgerClient(selected_profile.network)
        if selected_profile.network.faucet_url is not None:
            shell_globals["faucet"] = FaucetApi(selected_profile.network)

    wallets = {}
    print("Detecting local wallet keys...")
    try:
        for key in query_keychain_items():
            try:
                info = query_keychain_item(key)
                wallets[key] = LocalWallet(PrivateKey(info.private_key))
                print(f"Importing wallets['{key}']")
            except Exception:
                print(f"Failed to import local key '{key}'")
        print("Detecting local wallet keys...complete")
    except Exception:
        print("No local keychain found")

    shell_globals["cfg"] = cfg
    shell_globals["project_path"] = project_path
    shell_globals["profile"] = profile_name
    shell_globals["contracts"] = {contract.name: contract for contract in contracts}
    shell_globals["wallets"] = wallets
    for (name, instance) in contract_instances.items():
        shell_globals[name] = instance

    return shell_globals


def run(args: argparse.Namespace):
    shell_globals = load_config(args)
    shell_globals.update(globals())
    embed(shell_globals, vi_mode=False, history_filename=".shell_history")


def add_shell_command(parser):
    shell_cmd = parser.add_parser("shell")
    shell_cmd.add_argument(
        "-p", "--profile", default=None, help="The profile to use"
    )
    shell_cmd.set_defaults(handler=run)
