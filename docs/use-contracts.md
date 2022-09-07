# Contract Interaction

You can interact with your project's contracts by using the ```shell``` command:

```
jenesis shell
```
If a profile is not selected, the default profile will be selected automatically. You can specify any profile using the `--profile` optional argument:

```
jenesis shell --profile my_profile
```

You will observe the following text indicating the available contracts in your project.

```
Detecting contracts...
C my_first_contract
C cw20
Detecting contracts...complete
```
> *NOTE: `jenesis shell` currently requires that contract names use accepted python variable names. For example, using `my-first-contract` instead of `my_first_contract` will generate an error when trying to interact with it.*

In this case, we can see that `my_first_contract` and `cw20` contracts are available for this project. If these contracts have been already deployed you can directly interact with them by performing contract executions such as:

```
>>> my_first_contract.execute(args = {'msg_name': {...}}
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

We now proceed to deploy the cw20 contract, we define the arguments for the cw20 token: name, symbol, decimal, and the addresses that will be funded with these cw20 tokens. In this case we will fund wallet's address with 5000 tokens.
```
>>> cw20.deploy({"name": "Crab Coin","symbol": "CRAB","decimals": 6,"initial_balances": [{"address":wallet.address(),"amount":"5000"}]},wallet)
```


We can query wallet balance to make sure it has been funded with cw20 tokens

```
>>> cw20.query({"balance":{"address":wallet.address()}})
{'balance': '5000'}
```

We now execute a cw20 token transfer of 1000 tokens from wallet to wallet2

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
We can observe that wallet has sent 1000 tokens to wallet2.

You can also assemble the above commands into a script that is executable by the  ```run``` command.
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

If we paste the above code into the file script.py inside the project's directory, we can run it with:

```
jenesis run script.py
```

And you will observe the same output as before. You can also specify the profile as an optional argument using `--profile`.

You can visit [CosmPy](https://docs.fetch.ai/CosmPy/) for more contract interaction examples.
