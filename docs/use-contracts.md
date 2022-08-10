# Contract Interaction

You can interact with your project's contracts by using the ```shell``` command:

```
jenesis alpha shell
```

You will observe the following text indicating the available contracts in your project.

```
Detecting contracts...
C my-first-contract
C cw20
Detecting contracts...complete
```

In this case, we can see that my-first-contract and cw20 contracts are available for this project. If these contracts have been already deployed you can directly interact with them by performing contract executions such as:

```
>>> my-first-contract.execute(args = {""})
```

We will show an example assuming that the cw20 contract has only been compiled and not yet deployed, going through imports, deployment, execution, and querying.

First, we need to import the following from [cosmpy](https://docs.fetch.ai/CosmPy/)

```
>>> from cosmpy.aerial.client import LedgerClient, NetworkConfig
>>> from cosmpy.aerial.faucet import FaucetApi
>>> from cosmpy.crypto.address import Address
>>> from cosmpy.aerial.wallet import LocalWallet
```

Now we define the faucet and two wallets. We provide wealth to the sender wallet in atestfet so it can pay for transaction fees.

```
>>> faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
>>> wallet = LocalWallet.generate()
>>> wallet2 = LocalWallet.generate()
>>> faucet_api.get_wealth(wallet.address())
```

We now proceed to deploy the cw20 contract, we define the arguments for the cw20 token such as name, symbol, decimal, and the addresses that will be funded with these cw20 tokens.
```
>>> cw20.deploy({"name": "Crab Coin","symbol": "CRAB","decimals": 6,"initial_balances": [{"address":wallet.address(),"amount":"5000"}]},wallet)
```


We can query wallet balance to make sure it has cw20 balance

```
>>> cw20.query({"balance":{"address":wallet.address()}})
{'balance': '5000'}
```

We now execute a cw20 token transfer from wallet to wallet2

```
>>> cw20.execute({'transfer': {'amount':'1000','recipient':wallet2.address()}}, sender=wallet)
```

Finally, we query both wallet's balance

```
>>> cw20.query({"balance":{"address":wallet.address()}})
{'balance': '4000'}
>>> cw20.query({"balance":{"address":wallet2.address()}})
{'balance': '1000'}
```

To avoid running line by line in the terminal you can use the command ```run```. This command will read a specified python script with all the desired outcomes. This way we can put all together the example we just ran in the shell command in a single python script:

```python
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address
from cosmpy.aerial.wallet import LocalWallet

import time

faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
wallet = LocalWallet.generate()
faucet_api.get_wealth(wallet.address())
wallet2 = LocalWallet.generate()

cw20.deploy({"name": "Crab Coin","symbol": "CRAB","decimals": 6,"initial_balances": [{"address":wallet.address(),"amount":"5000"}]},wallet)
print("wallet initial cw20 balance: " , cw20.query({"balance":{"address":wallet.address()}}))

cw20.execute({'transfer': {'amount':'1000','recipient':wallet2.address()}}, sender=wallet)
print("transfering 1000 cw20 tokens from wallet to wallet2")
time.sleep(10)

print("wallet final cw20 balance: " , cw20.query({"balance":{"address":wallet.address()}}))
print("wallet2 final cw20 balance: " , cw20.query({"balance":{"address":wallet2.address()}}))
```

We simply named this script script.py and located it inside the project's directory. Now we simply run:

```
jenesis alpha run script.py
```

And you will observe the same output as before.

You can visit [CosmPy](https://docs.fetch.ai/CosmPy/) for more contract interaction examples.
