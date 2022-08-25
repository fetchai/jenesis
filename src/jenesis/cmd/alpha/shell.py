import argparse
import os

from cosmpy.aerial.client import LedgerClient
from ptpython import embed
from jenesis.config import Config
from jenesis.contracts.detect import detect_contracts
from jenesis.contracts.monkey import MonkeyContract
from jenesis.contracts.observer import DeploymentUpdater
from jenesis.network import run_local_node


def load_config(args: argparse.Namespace) -> dict:
    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        raise RuntimeError("Please run command from project root or create project first")

    cfg = Config.load(project_path)
    contracts = detect_contracts(project_path)

    contract_instances = {}

    profile_name = args.profile or cfg.get_default_profile()

    selected_profile = cfg.profiles.get(profile_name)
    if selected_profile is not None:
        if selected_profile.network.is_local:
            run_local_node(selected_profile.network)

        # build the ledger client
        client = LedgerClient(selected_profile.network)

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
                contract.binary_path,
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

    shell_globals = {}
    shell_globals["cfg"] = cfg
    shell_globals["project_path"] = project_path
    shell_globals["profile"] = profile_name
    shell_globals["contracts"] = {contract.name: contract for contract in contracts}
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
