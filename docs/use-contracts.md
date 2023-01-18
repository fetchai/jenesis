# Contract Interaction

You can interact with your project's contracts by using the ```shell``` or ```run``` commands.

## Previous steps

To reproduce the examples in this document, add and compile a basic starter contract and a cw20 token contract to your project with the following commands:

```bash
jenesis add contract starter my_first_contract -d deployment_1
jenesis add contract cw20-base my_token -d token_1
jenesis compile
```

For more contract template examples visit [Jenesis Templates](https://github.com/fetchai/jenesis-templates)

## Interactive Shell

To open a shell where you can easily interact with your contracts, run:
```bash
jenesis shell
```
If a profile is not selected, the default profile will be selected automatically. You can specify any profile using the `--profile` optional argument:

```bash
jenesis shell --profile my_profile
```

You will observe the following text indicating the available contracts in your project.

```
Network: fetchai-testnet
Detecting contracts...
C deployment_1
C token_1
Detecting contracts...complete
```
> *NOTE: `jenesis shell` currently requires that contract names use accepted python variable names. For example, using `token-1` instead of `token_1` will generate an error when trying to interact with it.*

In this case, we can see that `deployment_1` and `token_1` deployments are available for this project. If these contracts have been already deployed you can directly interact with them by performing contract querys and executions such as:

```python
>>> deployment_1.query(args = {'msg_name': {...}}
>>> deployment_1.execute(args = {'msg_name': {...}}
```

A ledger client (`ledger`) and your locally stored wallet keys will also be available in the shell. For example, if you have a local key named `alice`, you will find this under `wallets['alice']` and you can query the balance as follows:
```python
>>> ledger.query_bank_balance(wallets['alice'])
10000000000000000000
```

If the ledger is a testnet with a faucet url, you can get funds using the `faucet`:
```python
>>> faucet.get_wealth(wallets['alice'])
```

## Dynamic Methods

Jenesis also attaches the contract query, execution and deploy messages as dynamic methods.

For example, the following query

```python
>>> token_1.query({"balance": {"address": str(wallet.address())}}))
```
can also be run with:
```python
>>> token_1.balance(address=str(wallet.address()))
{'balance': '4000'}
```

Similarly, instead of using `token_1.execute...` , a transfer can be executed with:
```python
>>> token_1.transfer(amount='1000', recipient=str(wallet2.address()), sender=wallet)
```

Jensesis also has an autocompletion helper for query, execution and deployment arguments. It will show automatically when typing in the shell.


We will now show an example assuming that the `token_1` deployment contract has only been compiled and not yet deployed, going through deployment, execution, and querying using dynamic methods.

For this example, we will first generate two wallets. We provide wealth to the sender wallet in atestfet so it can pay for transaction fees.

```python
>>> wallet = LocalWallet.generate()
>>> wallet2 = LocalWallet.generate()
>>> faucet.get_wealth(wallet)
```

We now proceed to deploy `my_token` contract using `token_1` deployment configuration, we define the arguments for the cw20 token: name, symbol, decimal, and the addresses that will be funded with these cw20 tokens. In this case we will fund wallet's address with 5000 tokens.

```python
>>> token_1.deploy(name="Crab Coin", symbol="CRAB", decimals=6, initial_balances=[{ "address": str(wallet.address()), "amount" :  "5000"}], sender=wallet)
```

We can query wallet balance to make sure it has been funded with cw20 tokens

```python
>>> token_1.balance(address=str(wallet.address()))
{'balance': '5000'}
```

We now execute a cw20 token transfer of 1000 tokens from wallet to wallet2

```python
>>> token_1.transfer(amount='1000', recipient=str(wallet2.address()), sender=wallet)
```

Finally, we query both wallet's balance

```python
>>> token_1.balance(address=str(wallet.address()))
{'balance': '4000'}
>>> token_1.balance(address=str(wallet2.address()))
{'balance': '1000'}
```
We can observe that wallet has sent 1000 tokens to wallet2.

## Executing Scripts

You can also assemble the above commands into a script that is executable by the  ```run``` command:
```python
from cosmpy.aerial.wallet import LocalWallet

wallet = LocalWallet.generate()
faucet.get_wealth(wallet.address())
wallet2 = LocalWallet.generate()

token_1.deploy(name="Crab Coin", symbol="CRAB", decimals=6, initial_balances=[{ "address": str(wallet.address()), "amount" :  "5000"}], sender=wallet)

print("wallet initial cw20 MT balance: ", token_1.balance(address=str(wallet.address())))

tx = token_1.transfer(amount='1000', recipient=str(wallet2.address()), sender=wallet)
print("transfering 1000 cw20 MT tokens from wallet to wallet2")
tx.wait_to_complete()

print("wallet final cw20 MT balance: ", token_1.balance(address=str(wallet.address())))
print("wallet2 final cw20 MT balance: ", token_1.balance(address=str(wallet2.address())))
```

If we paste the above code into the file script.py inside the project's directory, we can run it with:

```
jenesis run script.py
```

And you will observe the same output as before. You can also specify the profile as an optional argument using `--profile`.

Finally, you can pass arguments to the script just as you would to a standard python script by placing all the arguments to the script after the `--` delimiter:
```
jenesis run script.py [--profile profile_name] -- arg1 arg2 --key1 value1 --key2 value2
```

You can visit [CosmPy](https://docs.fetch.ai/CosmPy/) for more contract interaction examples.
