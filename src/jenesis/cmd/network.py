import argparse
import os
from typing import Optional

from jenesis.config import Config
from jenesis.network import is_local_node_running, run_local_node, LedgerNodeDockerContainer


def get_profile(profile_name: Optional[str]):
    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        print("Please run command from project root")
        return None

    cfg = Config.load(project_path)
    return cfg, cfg.get_profile(profile_name)


def run_start(args: argparse.Namespace):
    cfg, profile = get_profile(args.profile)

    if profile is None:
        return 1

    if not profile.network.is_local:
        print("This profile is configured for a remote network.")
        return 1
    if run_local_node(profile.network, cfg.project_name, profile.name):
        return 0
    return 1


def run_stop(args: argparse.Namespace):
    cfg, profile = get_profile(args.profile)

    if profile is None:
        return 1

    if not profile.network.is_local:
        print("This profile is configured for a remote network.")
        return 1
    local_node = LedgerNodeDockerContainer(profile.network, cfg.project_name, profile.name)
    if local_node.container is not None:
        if local_node.is_ready():
            print("Shutting down local_node...")
            local_node.container.stop()
            print("Shutting down local_node...complete")
            return 0
        if is_local_node_running():
            print("The currently running local node does not match this project and profile. To stop this node, please stop it from the appropriate project and profile or by using Docker.")
    else:
        print("Did not find any local node for this profile")
    return 1


def add_network_command(parser):
    network_parser = parser.add_parser("network", help="Start or stop a local node")
    subparsers = network_parser.add_subparsers()

    netstart_cmd = subparsers.add_parser("start", help="Start local node")
    netstop_cmd = subparsers.add_parser("stop", help="Stop local node")
    for cmd in [netstart_cmd, netstop_cmd]:
        cmd.add_argument(
            "-p", "--profile", default=None, help="The profile associated with the network"
        )
    netstart_cmd.set_defaults(handler=run_start)
    netstop_cmd.set_defaults(handler=run_stop)
