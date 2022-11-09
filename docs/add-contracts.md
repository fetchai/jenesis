# Add contract templates
Once you have successfully created your project, you can add contract templates. You first need to navigate to your project's directory and run the following command:

```
jenesis add contract <TEMPLATE> <CONTRACT NAME> <DEPLOYMENTS> -p <PROFILE>
```
You can find all the contract templates available in [Jenesis Templates](https://github.com/fetchai/jenesis-templates).
An example of how to add the template **cw20** with the name `my_token` is given below:

```
jenesis add contract cw20-base my_token token_1 token_2
```

Since we didnt specify a profile, Jenesis will just use the default profile. As you can observe above, `token_1` and `token_2` deployments have been added, this will allow you to deploy `my_token` with two different configurations. You can add as many deployments as you wish.

This ```add contract``` command will add a contract template to your jenesis project inside `contracts/my_token/` folder. It will also update the `jenesis.toml` configuration file with the contract information under the selected profile.

```
[profile.testing.contracts.token_1]
name = "token_1"
contract = "my_token"
network = "fetchai-testnet"
deployer_key = ""
init_funds = ""

[profile.testing.contracts.token_2]
name = "token_2"
contract = "my_token"
network = "fetchai-testnet"
deployer_key = ""
init_funds = ""

[profile.testing.contracts.token_1.init]

[profile.testing.contracts.token_2.init]
```

The `deployer_key` field can be manually specified, you can choose any private key locally available to deploy any specific contract. You can also leave this field empty since the ```deploy``` command has an optional argument to deploy all contracts inside a specified profile with the same key, overriding this `deployer_key` argument in the `jenesis.toml` file. See [deploy contracts](deploy-contracts.md) for more information. 

Finally, the `init` section contains the parameters needed in the instantiation message for this contract to be deployed. The required parameters are taken from the schema file inside the `contracts` directory. Since this contract templat doesnt include a schema, it will be generated when [compiling](compile-contracts.md) the contract `my_token` loading the init fields to the `jenesis.toml` file. You will need to manually add the values for these parameters in their correct variable type, which are listed on the schema file. For this  **my_token** contract, we need to fill the following init fields for each deployment after [compiling](compile-contracts.md). Here is an example:

```
[profile.testing.contracts.token_1.init]
decimals = 6
name = "my_token_name"
symbol = "SYMBOL"
initial_balances = [{ address = "fetch1d25ap9danl4726uk2nt307y630v87h3h2vq6pl", amount =  "5000"}]

[profile.testing.contracts.token_2.init]
decimals = 6
name = "my_token_name_2"
symbol = "SYMBOL"
initial_balances = [{ address = "fetch1d25ap9danl4726uk2nt307y630v87h3h2vq6pl", amount =  "2000"}]
```

If your contract requires nested instantiation messages you may add fields following this structure:

```
[profile.testing.contracts.example-nested-contract.init]
price = {amount = 1000, denom = DLS}
info = {performance = {max_speed = 200, unit = kph}, fuel = {consumption = 7, unit = kmpl}}
```
> *NOTE: Before editing the `jenesis.toml` configuration file with the desired `deployer_key` and `init` parameters, make sure to first [compile](compile-contracts.md) your contract. All configuration parameters will restart every time a contract is compiled to make sure everything is up to date.*


# Add contract deployments
You can also add further deployments for a given contract by specifying the contract name and the deployment name. If we want to add a third token called `token_3` using `my_token` contract, we can run:  

```
jenesis add deployment my_token token_3
```
This will automatically create another deployment entry called `token_3`.

# Attach deployed contracts

If you add a contract into the project's contract folder that has already been deployed in the network, you can attach the deployment to your project for future interaction using the ```attach``` command.

To add a deployment to yout project you can run:

```
jenesis add contract cw20-base my_token token_1
```

Then compile the contract:

```
jenesis compile
```

To attach the contract, you will need to specify the deployment's name and address. You can optionally specify the profile where you wish to insert the contract into. If this is not specified, the deployment will be attached to the default profile, which is the first profile created in your project, unless the `default` settings are manually changed.

```
jenesis attach token_1 fetch18xs97q6h9zgh4sz730a42pp0dqa9sh4eef7eutfkv69q3v2y3x8s72pkua
```

This will add the relevant deployment information into a `jenesis.lock` file and you will now be able to interact with `token_1` using [contract interactions](use-contracts.md) 
