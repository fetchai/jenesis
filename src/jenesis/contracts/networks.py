from cosmpy.aerial.config import NetworkConfig
from jenesis.node import Network

LOCAL_NODES = ['fetchai-localnode']

def fetchai_testnet_config() -> Network:
    return Network.from_cosmpy_config("fetchai-testnet", NetworkConfig.fetchai_stable_testnet())

def fetchai_localnode_config() -> Network:
    return Network.from_cosmpy_config(
        "fetchai-localnode",
        NetworkConfig(
            chain_id="localnode",
            url="rest+http://127.0.0.1:1317",
            fee_minimum_gas_price=5000000000,
            fee_denomination="atestfet",
            staking_denomination="atestfet",
        ),
        is_local=True,
    )
