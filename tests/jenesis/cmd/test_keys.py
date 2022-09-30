import subprocess
import pytest

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    key = "sample_key"
    subprocess.run("fetchd keys add " + key, shell=True)

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    assert key_address == subprocess.getoutput('jenesis keys show ' + key)