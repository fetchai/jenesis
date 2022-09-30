import subprocess
import pytest

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    subprocess.run("fetchd config keyring-backend test", shell=True)

    key = "sample_key"
    subprocess.run("fetchd keys add " + key, shell=True)

    #key_address = subprocess.getoutput("fetchd keys show -a " + key)
    key_address = subprocess.getoutput("fetchd keys add " + key)

    #jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == "test"