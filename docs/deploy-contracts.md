# Deploy contracts

Once you have successfully compiled your contracts, make sure to fill out the necessary instantiation message information under the `init` field in the `jenesis.toml` file.

> *Note: `jenesis deploy` currently requires that each contract's directory name matches the `.wasm` file name under the `artifacts` directory.

To deploy all the contracts inside a profile you have two options: 

1. Fill the `deployer_key` field for each contract inside the `jenesis.toml` file (keys can be different for each contract) and run the following command:

```
jenesis deploy [--profile profile_name]
```
Each contract inside the specified profile will be deployed with the specified key.

2. Simply specify a certain key as an argument of the deploy command:

```
jenesis deploy key_name [--profile profile_name]
```

The `deployer_key` field will be ignored in this case and all contracts inside the specified profile will be deployed using the key `key_name`.

After running either of the commands mentioned above, all the deployment information will be saved in the `jenesis.lock` file inside your project's directory


```toml
[profile.testing.my_first_contract]
checksum = "ecf640a7512be3777c72ec42aff01fdb22897b71953011af3c41ee5dbf3d3bc5"
digest = "be4a4bdfeb4ed8f504c7b7ac84e31ad3876627398a6586b49cac586633af8b85"
address = "fetch16l239ggyr4z7pvsxec0ervlyw03mn6pz62l9ss6la94cf06awv0q36cq7u"
code_id = 2594
```

## Deploy contracts that depend on other deployments

You can point to other contract addresses in any contract's instantiation message if required. 
For example: if you have contracts `A`, `B`, and `C` within your project, but contract `A` requires contract's `B` deployment address in its instantiation message and contract `B` requires contract's `C` deployment address, they will need to be deployed in the following order: `C`, `B`, `A`. In order to provide this information to `Jenesis` you will need to specify where exactly these contract addresses need to be inserted inside the instantiation messages. You can do this by writing the `$` symbol followed by the contract name in the corresponding field in the init parameters:


```toml
[profile.testing.contracts.A.init]
name = "A"
token_contract_address = "$B"

[profile.testing.contracts.B.init]
token_name = "my_token"
liquidity_contract_address = "$C"

[profile.testing.contracts.C.init]
count = 5
```

Finally, `Jenesis` will detect this information and deploy the contracts in the correct order: `C`, `B`, `A`.
