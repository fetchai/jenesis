import subprocess
import pytest

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    key = "zz"
    subprocess.run("fetchd keys add " + key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == jenesis_key_address 



