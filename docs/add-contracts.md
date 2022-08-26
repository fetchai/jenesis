# Add contract templates
Once you have successfully created your project, you can add contract templates. You first need to navigate to your project's directory and run the following command:

```
jenesis add contract <TEMPLATE> <NAME>
```

An example of how to add the template **starter** with the name `my_first_contract` is given below:

```
jenesis add contract starter my_first_contract
```

This ```add contract``` command will add a contract template to your jenesis project inside `contracts/my_first_contract/` folder. It will also update the `jenesis.toml` configuration file with the contract information under all existing profiles.

```
[profile.my_profile.contracts.my_first_contract]
contract = "my_first_contract"
network = "fetchai-testnet"
deployer_key = ""

[profile.my_profile.contracts.my_first_contract.init]
count = ""
```
The `deployer_key` field can be manually specified, you can choose any private key locally available to deploy any specific contract. You can also leave this field empty since the ```deploy``` command has an optional argument to deploy all contracts inside a specified profile with the same key, overriding this `deployer_key` argument in the `jenesis.toml` file. See [deploy contracts](deploy-contracts.md) for more information. 

Finally, the `init` section contains the parameters needed in the instantiation message for this contract to be deployed. The required parameters are taken from the `instantiate_msg.json` file inside the `contracts` directory. You will need to manually add the values for these parameters in their correct variable type, which are listed in `contracts/my_first_contract/schema/instantiate_msg.json`. For this contract **my_first_contract** we need to add an integer value to the `count` field.

```
[profile.my_profile.contracts.my_first_contract.init]
count = 10
```

If your contract requires nested instantiation messages you may add fields following this structure:

```
[profile.testing.contracts.example-nested-contract.init]
price = {amount = 1000, denom = DLS}
info = {performance = {max_speed = 200, unit = kph}, fuel = {consumption = 7, unit = kmpl}}
```

You can also add contracts manually by copying and pasting the contract directory from another project you may have, however, they need to follow the same directory structure as the **starter** template mentioned above.

# Attach deployed contracts

If you have added a contract into the project's contract folder that has already been deployed in the network, you can attach it to your project for future interaction using the ```attach``` command. You will need to specify the contract's name and deployment address. You can optionally specify the profile where you wish to insert the contract into. If this is not specified, the deployment will be attached to the default profile, which is the first profile created in your project, unless the `default` settings are manually changed.

```
jenesis attach my_first_contract fetch18xs97q6h9zgh4sz730a42pp0dqa9sh4eef7eutfkv69q3v2y3x8s72pkua
```

This will add the relevant deployment information into a `jenesis.lock` file and you will now be able to interact with `my_first_contract` using [contract interactions](use-contracts.md) 
