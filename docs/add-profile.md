You can add more profiles than the one specified using the ```new``` command by running the following ```add profile``` command:

```
jenesis add profile my_second_profile
```
By default, the profile's network will be set to `fetchai-testnet`, but you can specify it using the `--network` optional argument. The following will be added to the existing information in your `jenesis.toml` file:

```toml
[profile.my_second_profile.network]
name = "fetchai-testnet"
chain_id = "dorado-1"
fee_minimum_gas_price = 5000000000
fee_denomination = "atestfet"
staking_denomination = "atestfet"
url = "grpc+https://grpc-dorado.fetch.ai"
faucet_url = "https://faucet-dorado.fetch.ai"
is_local = false

[profile.my_second_profile.contracts]
```
If there are existing contracts in your project, all of them will be added to the new profile.