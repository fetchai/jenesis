from typing import Optional

from cosmpy.aerial.config import NetworkConfig


def get_network_config(name: str) -> Optional[NetworkConfig]:
    if name == 'fetchai-capricorn':
        return NetworkConfig.capricorn_testnet()
    return None
