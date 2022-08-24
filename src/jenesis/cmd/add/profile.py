import argparse
import os
import toml

from jenesis.config import Config, ConfigurationError
from jenesis.contracts.networks import fetchai_testnet_config, fetchai_localnode_config

def run(args: argparse.Namespace):

    project_path = os.getcwd()

    # check that we are actually running the command from the project root
    if not os.path.exists(os.path.join(project_path, "jenesis.toml")):
        # pylint: disable=all
        print("Please run command from project root")
        return

    data = toml.load("jenesis.toml")

    if args.network == "fetchai-testnet":
        net_config = fetchai_testnet_config()
    elif args.network == "fetchai-localnode":
        net_config = fetchai_localnode_config()
    else:
        raise ConfigurationError("Network name not recognized")

    network = {"name": "fetchai-testnet"}
    network.update(vars(net_config))

    data["profile"][args.profile] = {
        "network": network,
        "contracts": {}
    }

    output_file_name = "jenesis.toml"
    with open(output_file_name, "w") as toml_file:
        toml.dump(data, toml_file)


def add_profile_command(parser):
    profile_cmd = parser.add_parser("profile")
    profile_cmd.add_argument("profile", default="testing", help="The profile to create"
    )
    profile_cmd.add_argument(
        "-n", "--network", default="fetchai-testnet", help="Network to use"
    )
    profile_cmd.set_defaults(handler=run)