import argparse
import os
import sys

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from ptpython import embed
from jenesis.config import Config, Profile
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.contracts.observer import DeploymentUpdater
from jenesis.keyring import query_keychain_items, query_keychain_item
from jenesis.network import network_context


PROJECT_PATH = os.getcwd()


def get_profile(cfg: Config, args: argparse.Namespace) -> Profile:

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(PROJECT_PATH, "jenesis.toml")):
        raise RuntimeError("Please run command from project root or create project first")

    if args.profile is not None and args.profile not in cfg.profiles:
        print(f'Invalid profile name. Expected one of {",".join(cfg.profiles.keys())}')
        sys.exit(1)

    profile_name = args.profile or cfg.get_default_profile()

    return cfg.profiles.get(profile_name)


def load_shell_globals(cfg: Config, selected_profile: Profile) -> dict:

    shell_globals = {}
    contract_instances = {}

    contracts = {contract.name: contract for contract in detect_contracts(PROJECT_PATH)}

    deployments = selected_profile.deployments

    if selected_profile is not None:

        # build the ledger client
        client = LedgerClient(selected_profile.network)

        print(f'Network: {selected_profile.network.name}')

        print('Detecting contracts...')

        for (deployment_name, deployment) in deployments.items():
            contract = contracts[deployment.contract]
            print("C", deployment_name)

            # skip contracts that we have not compiled
            if contract.digest() is None:
                continue

            monkey = MonkeyContract(
                contract,
                client,
                address=deployment.address,
                code_id=deployment.code_id,
                observer=DeploymentUpdater(
                    cfg,
                    PROJECT_PATH,
                    selected_profile.name,
                    deployment_name,
                ),
                init_args=deployment.init,
            )

            contract_instances[deployment_name] = monkey

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
    shell_globals["project_path"] = PROJECT_PATH
    shell_globals["profile"] = selected_profile.name
    shell_globals["contracts"] = contracts
    shell_globals["wallets"] = wallets
    for (name, instance) in contract_instances.items():
        shell_globals[name] = instance

    return shell_globals


def run(args: argparse.Namespace):
    cfg = Config.load(PROJECT_PATH)
    profile: Profile = get_profile(cfg, args)
    shell_globals = globals()

    with network_context(profile.network, cfg.project_name, profile.name):
        shell_globals.update(load_shell_globals(cfg, profile))
        embed(shell_globals, vi_mode=False, history_filename=".shell_history")


def add_shell_command(parser):
    shell_cmd = parser.add_parser("shell")
    shell_cmd.add_argument(
        "-p", "--profile", default=None, help="The profile to use"
    )
    shell_cmd.set_defaults(handler=run)
