import os
import tempfile
import time
from typing import Optional, List

from docker import from_env
from docker.errors import DockerException
from docker.types import Mount

from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.client import LedgerClient

DEFAULT_DOCKER_IMAGE_TAG = "fetchai/fetchd:0.10.5"
DEFAULT_VALIDATOR_KEY_NAME = "validator"
DEFAULT_MNEMONIC = "gap bomb bulk border original scare assault pelican resemble found laptop skin gesture height inflict clinic reject giggle hurdle bubble soldier hurt moon hint"
DEFAULT_PASSWORD = "12345678"
DEFAULT_MONIKER = "test-node"
DEFAULT_CHAIN_ID = "testing"
DEFAULT_GENESIS_ACCOUNT = "fetch1gns5lphdk5ew5lnre7ulzv8s8k9dr9eyqvgj0w"
DEFAULT_DENOMINATION = "atestfet"
DEFAULT_CLI_BINARY = "fetchd"

TMP_DIR = tempfile.TemporaryDirectory() # pylint: disable=consider-using-with

class Network(NetworkConfig):

    def __init__(
        self,
        name: str = "",
        chain_id: str = "",
        fee_minimum_gas_price: int = 0,
        fee_denomination: str = "",
        staking_denomination: str = "",
        url: str = "",
        faucet_url: Optional[str] = None,
        is_local: Optional[bool] = False,
        cli_binary: Optional[str] = None,
        validator_key_name: Optional[str] = None,
        mnemonic: Optional[str] = None,
        password: Optional[str] = None,
        moniker: Optional[str] = None,
        genesis_accounts: Optional[List[str]] = None,
        debug_trace: bool = True,
    ):
        super().__init__(
            chain_id,
            fee_minimum_gas_price,
            fee_denomination,
            staking_denomination,
            url,
            faucet_url=faucet_url,
        )
        self.name = name
        self.is_local = is_local
        if is_local:
            self.cli_binary = cli_binary or DEFAULT_CLI_BINARY
            self.validator_key_name = validator_key_name or DEFAULT_VALIDATOR_KEY_NAME
            self.mnemonic = mnemonic or DEFAULT_MNEMONIC
            self.password = password or DEFAULT_PASSWORD
            self.moniker = moniker or DEFAULT_MONIKER
            self.genesis_accounts = genesis_accounts or [DEFAULT_GENESIS_ACCOUNT]
            self.debug_trace = debug_trace

    @classmethod
    def from_cosmpy_config(cls, name: str, net_config: NetworkConfig, is_local: bool = False):
        return Network(
            name,
            net_config.chain_id,
            net_config.fee_minimum_gas_price,
            net_config.fee_denomination,
            net_config.staking_denomination,
            net_config.url,
            faucet_url=net_config.faucet_url,
            is_local=is_local,
        )


class LedgerNodeDockerContainer:

    PORTS = {9090: 9090, 1317: 1317, 26657: 26657}

    def __init__(
        self,
        network: Network,
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
        self.network: Network = network

    @property
    def tag(self) -> str:
        """Get the image tag."""
        return self._image_tag

    def _make_entrypoint_file(self, tmpdirname) -> None:
        """Make a temporary entrypoint file to setup and run the test ledger node"""
        trace_flag = '--trace' if self.network.debug_trace else ''
        run_node_lines = [
            "#!/usr/bin/env bash",
            # variables
            f'export VALIDATOR_KEY_NAME={self.network.validator_key_name}',
            f'export VALIDATOR_MNEMONIC="{self.network.mnemonic}"',
            f'export PASSWORD="{self.network.password}"',
            f'export CHAIN_ID={self.network.chain_id}',
            f'export MONIKER={self.network.moniker}',
            f'export DENOM={self.network.fee_denomination}',
            # Add key
            f'( echo "$VALIDATOR_MNEMONIC"; echo "$PASSWORD"; echo "$PASSWORD"; ) |{self.network.cli_binary} keys add $VALIDATOR_KEY_NAME --recover',
            # Configure node
            f"{self.network.cli_binary} init --chain-id=$CHAIN_ID $MONIKER",
        ]
        for acc in self.network.genesis_accounts:
            run_node_lines.append(
                f'echo "$PASSWORD" |{self.network.cli_binary} add-genesis-account {acc} 100000000000000000000000$DENOM',
            )
        run_node_lines.extend([
            f'echo "$PASSWORD" |{self.network.cli_binary} add-genesis-account $({self.network.cli_binary} keys show $VALIDATOR_KEY_NAME -a) 100000000000000000000000$DENOM',
            f'echo "$PASSWORD" |{self.network.cli_binary} gentx $VALIDATOR_KEY_NAME 10000000000000000000000$DENOM --chain-id $CHAIN_ID',
            f"{self.network.cli_binary} collect-gentxs",
            # Enable rest-api
            f'sed -i "s/stake/atestfet/" ~/.{self.network.cli_binary}/config/genesis.json',
            f'sed -i "s/enable = false/enable = true/" ~/.{self.network.cli_binary}/config/app.toml',
            f'sed -i "s/swagger = false/swagger = true/" ~/.{self.network.cli_binary}/config/app.toml',
            f"{self.network.cli_binary} start --rpc.laddr tcp://0.0.0.0:26657 {trace_flag}",
        ])
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

    @classmethod
    def is_ready(cls) -> bool:
        try:
            net_config = fetchai_localnode_config()
            client = LedgerClient(net_config)
            validators = client.query_validators()
            assert len(validators) > 0
            return True
        except Exception:
            return False

    @classmethod
    def wait_until_ready(cls, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        for _ in range(max_attempts):
            if cls.is_ready():
                return True
            time.sleep(sleep_rate)
        return False


def run_local_node(network: Network):
    try:
        local_node = LedgerNodeDockerContainer(network)
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
    except DockerException as ex:
        print(f"Failed to start local node: looks like your docker setup isn't right, please visit https://jenesis.fetch.ai/ for more information:\n\n{ex}")


def fetchai_testnet_config() -> Network:
    return Network.from_cosmpy_config("fetchai-testnet", NetworkConfig.fetchai_stable_testnet())


def fetchai_localnode_config() -> Network:
    return Network.from_cosmpy_config(
        "fetchai-localnode",
        NetworkConfig(
            chain_id="localnode",
            url="grpc+http://127.0.0.1:9090/",
            fee_minimum_gas_price=5000000000,
            fee_denomination="atestfet",
            staking_denomination="atestfet",
        ),
        is_local=True,
    )
