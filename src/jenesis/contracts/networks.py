from typing import Optional

from cosmpy.aerial.config import NetworkConfig

LOCAL_NODES = ['fetchai-localnode']

def get_network_config(name: str) -> Optional[NetworkConfig]:
    if name == 'fetchai-testnet':
        return NetworkConfig.latest_stable_testnet()
    if name == 'fetchai-localnode':
        return NetworkConfig(
            chain_id="localnode",
            url="rest+http://127.0.0.1:1317",
            fee_minimum_gas_price=5000000000,
            fee_denomination="atestfet",
            staking_denomination="atestfet",
        )
    return None
