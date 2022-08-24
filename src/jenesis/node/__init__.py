import os
import tempfile
import time
from typing import Optional, List

from docker import from_env
from docker.types import Mount
import requests

from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.client import parse_url

DEFAULT_DOCKER_IMAGE_TAG = "fetchai/fetchd:0.10.5"
DEFAULT_MNEMONIC = "gap bomb bulk border original scare assault pelican resemble found laptop skin gesture height inflict clinic reject giggle hurdle bubble soldier hurt moon hint"
DEFAULT_PASSWORD = "12345678"
DEFAULT_MONIKER = "test-node"
DEFAULT_CHAIN_ID = "testing"
DEFAULT_GENESIS_ACCOUNT = "validator"
DEFAULT_DENOMINATION = "atestfet"
DEFAULT_CLI_BINARY = "fetchd"

TMP_DIR = tempfile.TemporaryDirectory() # pylint: disable=consider-using-with

class LocalNodeConfig(NetworkConfig):

    def __init__(
        self,
        net_config: NetworkConfig,
        cli_binary: Optional[str] = DEFAULT_CLI_BINARY,
        mnemonic: Optional[str] = DEFAULT_MNEMONIC,
        password: Optional[str] = DEFAULT_PASSWORD,
        moniker: Optional[str] = DEFAULT_MONIKER,
        genesis_accounts: Optional[List[str]] = None,
    ):
        self.cli_binary = cli_binary
        self.mnemonic = mnemonic
        self.password = password
        self.moniker = moniker
        self.genesis_accounts = genesis_accounts or [DEFAULT_GENESIS_ACCOUNT]
        super().__init__(
            net_config.chain_id,
            net_config.fee_minimum_gas_price,
            net_config.fee_denomination,
            net_config.staking_denomination,
            net_config.url,
            faucet_url=net_config.faucet_url,
        )

class LedgerNodeDockerContainer:

    PORTS = {1317: 1317, 26657: 26657}

    def __init__(
        self,
        config: dict,
        tag: str = DEFAULT_DOCKER_IMAGE_TAG,
    ):
        """
        Initialize the Fetch ledger Docker image.

        :param client: the Docker client.
        :param addr: the address.
        :param port: the port.
        :param config: optional configuration to command line.
        """
        self._client = from_env()
        self._image_tag = tag
        self.config: LocalNodeConfig = config

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return self._image_tag

    def _make_entrypoint_file(self, tmpdirname) -> None:
        """Make a temporary entrypoint file to setup and run the test ledger node"""
        run_node_lines = (
            "#!/usr/bin/env bash",
            # variables
            f'export VALIDATOR_KEY_NAME={self.config.genesis_accounts[0]}',
            f'export VALIDATOR_MNEMONIC="{self.config.mnemonic}"',
            f'export PASSWORD="{self.config.password}"',
            f'export CHAIN_ID={self.config.chain_id}',
            f'export MONIKER={self.config.moniker}',
            f'export DENOM={self.config.fee_denomination}',
            # Add key
            f'( echo "$VALIDATOR_MNEMONIC"; echo "$PASSWORD"; echo "$PASSWORD"; ) |{self.config.cli_binary} keys add $VALIDATOR_KEY_NAME --recover',
            # Configure node
            f"{self.config.cli_binary} init --chain-id=$CHAIN_ID $MONIKER",
            f'echo "$PASSWORD" |{self.config.cli_binary} add-genesis-account $({self.config.cli_binary} keys show $VALIDATOR_KEY_NAME -a) 100000000000000000000000$DENOM',
            f'echo "$PASSWORD" |{self.config.cli_binary} gentx $VALIDATOR_KEY_NAME 10000000000000000000000$DENOM --chain-id $CHAIN_ID',
            f"{self.config.cli_binary} collect-gentxs",
            # Enable rest-api
            f'sed -i "s/stake/atestfet/" ~/.{self.config.cli_binary}/config/genesis.json',
            f'sed -i "s/enable = false/enable = true/" ~/.{self.config.cli_binary}/config/app.toml',
            f'sed -i "s/swagger = false/swagger = true/" ~/.{self.config.cli_binary}/config/app.toml',
            f"{self.config.cli_binary} start --rpc.laddr tcp://0.0.0.0:26657",
        )

        entrypoint_file = os.path.join(tmpdirname, "run-node.sh")
        with open(entrypoint_file, "w", encoding="utf-8") as file:
            file.writelines(line + "\n" for line in run_node_lines)
        os.chmod(entrypoint_file, 300)

    def run(self):
        self._make_entrypoint_file(TMP_DIR.name)
        mount_path = "/mnt"
        volumes = {TMP_DIR.name: {"bind": mount_path, "mode": "rw"}}
        entrypoint = os.path.join(mount_path, "run-node.sh")
        container = self._client.containers.run(
            self.tag,
            detach=True,
            volumes=volumes,
            entrypoint=str(entrypoint),
            ports=self.PORTS,
        )
        return container

    def is_ready(self) -> bool:
        try:
            parsed_url = parse_url(self.config.url)
            url = f"{parsed_url.rest_url}/blocks/latest"
            response = requests.get(url)
            assert response.status_code == 200, ""
            return True
        except Exception:
            return False

    def wait_until_ready(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        for _ in range(max_attempts):
            if self.is_ready():
                return True
            time.sleep(sleep_rate)
        return False


def run_local_node(net_config: NetworkConfig):
    local_node_config = LocalNodeConfig(net_config)
    local_node = LedgerNodeDockerContainer(local_node_config)
    if not local_node.is_ready():
        print("Starting local node...")
        container = local_node.run()
        if not container.status == "created":
            raise RuntimeError('Failed to create local node.')
        if not local_node.wait_until_ready():
            raise RuntimeError('Failed to start local node.')
        print("Stating local node...complete")
    else:
        print("Detected local node already running.")
