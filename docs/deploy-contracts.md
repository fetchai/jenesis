# Deploy contracts

> *NOTE: ```deploy``` command is still under active development and currently only supported in MacOS*

Once you have successfully compiled your contracts, make sure to fill out the necessary instantiation message information under the `init` field in the `jenesis.toml` file. 

> *Note: `jenesis deploy` currently requires that each contract's directory name matches the `.wasm` file name under the `artifacts` directory.

To deploy all the contracts inside a certain profile you have two options: 

1. Fill the `deployer_key` field for each contract (they can be different) and run the following command:

```
jenesis alpha deploy profile_name
```
Each contract inside the specified profile will be deployed with the specified key.

2. Simply specify a certain key as an argument of the deploy command:

```
jenesis alpha deploy profile_name key_name
```

The `deployer_key` field will be ignored in this case and all contracts inside the specified profile will be deployed using the key `key_name`.

After running either of the commands mentioned above, all the deployment information will be saved in the `jenesis.lock` file inside your project's directory

```
[profile.testing.my_first_contract]
checksum = "ecf640a7512be3777c72ec42aff01fdb22897b71953011af3c41ee5dbf3d3bc5"
digest = "be4a4bdfeb4ed8f504c7b7ac84e31ad3876627398a6586b49cac586633af8b85"
address = "fetch16l239ggyr4z7pvsxec0ervlyw03mn6pz62l9ss6la94cf06awv0q36cq7u"
code_id = 2594
```