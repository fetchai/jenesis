# Add contract templates
Once you have successfully created your project, you can add contract templates. You first need to navigate to your project's directory and run the following command:

```
jenesis add contract <TEMPLATE> <NAME>
```

An example of how to add the template **starter** with the name `my_first_contract` is given below:

```
jenesis add contract starter my_first_contract
```

This ```add contract``` command will add a contract template to your jenesis project inside `contracts/my_first_contract/` folder. It will also update the `jenesis.toml` configuration file with the contract information:

```
[profile.testing.contracts.my_first_contract]
contract = "my_first_contract"
network = "fetchai-testnet"
deployer_key = ""

[profile.testing.contracts.my_first_contract.init]
count = ""
```
The `deployer_key` field can be manually specified, you can choose any private key locally available to deploy any specific contract. You can also leave this field empty since the ```deploy``` command has an optional argument to deploy all contracts inside a specified profile with the same key, overriding this `deployer_key` argument in the `jenesis.toml` file. See [deploy contracts](deploy-contracts.md) for more information. 

Finally, the `init` section contains the parameters needed in the instantiation message for this contract to be deployed. The required parameters are taken from the `instantiate_msg.json` file inside the `contracts` directory. You will need to manually add the values for these parameters in their correct variable type, which are listed in `contracts/my_first_contract/schema/instantiate_msg.json`. For this contract **my_first_contract** we need to add an integer value to the `count` field.

```
[profile.testing.contracts.my_first_contract.init]
count = 10
```

If your contract requires nested instantiation messages you may add fields following this structure:

```
[profile.testing.contracts.example-nested-contract.init]
price = {amount = 1000, denom = DLS}
info = {performance = {max_speed = 200, unit = kph}, fuel = {consumption = 7, unit = kmpl}}
```

You can also add contracts manually by copying and pasting the contract directory from another project you may have, however, they need to follow the same directory structure as the **starter** template mentioned above. If you add a contract manually, you will need to run ```jenesis init``` again to update the `jenesis.toml` configuration file.
