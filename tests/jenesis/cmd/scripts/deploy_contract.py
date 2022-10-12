from cosmpy.aerial.wallet import LocalWallet

wallet = LocalWallet.generate()
faucet.get_wealth(wallet.address())

contract.deploy({"count":5}, wallet)

tx = contract.reset(wallet, count=8)
tx.wait_to_complete()

result = contract.get_count()
print("jenesis run output:"+str(result))