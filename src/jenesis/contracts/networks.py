from typing import Optional

from cosmpy.aerial.config import NetworkConfig, NetworkConfigError

LOCAL_NODES = ['fetchai-localnode']

def get_network_config(network: dict) -> Optional[NetworkConfig]:
    net_config = NetworkConfig(
        chain_id=network["chain_id"],
        url=network["url"],
        fee_minimum_gas_price=network["fee_minimum_gas_price"],
        fee_denomination=network["fee_denomination"],
        staking_denomination=network["staking_denomination"],
    )
    try:
        net_config.validate()
    except NetworkConfigError as ex:
        print(f"No valid network configuration found: {ex}")
        return None
    return net_config

def fetchai_testnet_config() -> NetworkConfig:
    return NetworkConfig.latest_stable_testnet()

def fetchai_localnode_config() -> NetworkConfig:
    return NetworkConfig(
        chain_id="localnode",
        url="rest+http://127.0.0.1:1317",
        fee_minimum_gas_price=5000000000,
        fee_denomination="atestfet",
        staking_denomination="atestfet",
    )
