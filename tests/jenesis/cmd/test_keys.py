import subprocess

from jenesis.contracts.detect import detect_contracts
from jenesis.network import fetchai_testnet_config

# Unfinished
def test_keys():
    """Test key command"""

    key = "sample_key"
    subprocess.run("fetchd keys add " + key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    # Requires password:
    # assert type(key_address) == type(subprocess.getoutput('jenesis alpha keys show ' + key))