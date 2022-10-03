import subprocess
import pytest

#@pytest.mark.skip
def test_keys():
    """Test key command"""

    #subprocess.run("fetchd config keyring-backend test", shell=True)

    key = "zz"

    #x = subprocess.run("echo 'password' | gnome-keyring-daemon --unlock", shell=True, capture_output=True)  

    #print( 'exit statusx:', x.returncode )
    #print( 'stdoutx:', x.stdout.decode() )
    #print( 'stderrx:', x.stderr.decode() )

    p = subprocess.run("fetchd keys add " + key, shell=True, capture_output=True)

    print( 'exit status:', p.returncode )
    print( 'stdout:', p.stdout.decode() )
    print( 'stderr:', p.stderr.decode() )

    key_address = subprocess.getoutput("fetchd keys show -a " + key)

    jenesis_key_address = subprocess.getoutput("jenesis keys show " + key)

    assert key_address == jenesis_key_address 



