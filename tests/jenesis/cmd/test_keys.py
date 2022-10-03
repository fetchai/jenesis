import subprocess
import pytest

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    #subprocess.run("fetchd config keyring-backend test", shell=True)

    key = "zz"

    ID = subprocess.getoutput("gpg --generate-key")
    subprocess.run("pass init "+ ID, shell=True)  

    p = subprocess.run("fetchd keys add " + key, shell=True, capture_output=True)

    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )
    print( 'stderr:', p.stderr.decode() )

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == jenesis_key_address 



